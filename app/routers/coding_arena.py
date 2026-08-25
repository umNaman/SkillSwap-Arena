import secrets
import string
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (ArenaProfile, ArenaTransaction, AttackSession, BattleStatus,
    CodingBattle, CodingSubmission, HintUnlock, ProblemCommunityStat)
from app.schemas.coding_arena import ArenaFilters, HintRequest, JoinRoomRequest, RunRequest, SubmitRequest
from app.services.code_execution import get_execution_provider, outputs_match
from app.services.problem_catalog import BY_ID, PROBLEMS, select_problem
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/api/coding", tags=["Coding Arena"])


def _alias(user) -> str:
    return (user.default_alias or "Anonymous Coder")[:32]


async def _profile(db: AsyncSession, user_id: uuid.UUID) -> ArenaProfile:
    profile = await db.get(ArenaProfile, user_id)
    if profile:
        return profile
    profile = ArenaProfile(user_id=user_id, points=200)
    db.add(profile)
    db.add(ArenaTransaction(user_id=user_id, amount=200, reason="WELCOME", event_key="welcome"))
    try:
        await db.flush()
        return profile
    except IntegrityError:
        await db.rollback()
        profile = await db.get(ArenaProfile, user_id)
        if not profile: raise
        return profile


async def _add_points(db, profile, amount: int, reason: str, event_key: str, problem_id: str | None = None) -> bool:
    exists = await db.scalar(select(ArenaTransaction.id).where(
        ArenaTransaction.user_id == profile.user_id, ArenaTransaction.event_key == event_key))
    if exists:
        return False
    if profile.points + amount < 0:
        raise HTTPException(409, "Not enough Arena Points")
    profile.points = max(0, profile.points + amount)
    db.add(ArenaTransaction(user_id=profile.user_id, amount=amount, reason=reason,
                            event_key=event_key, problem_id=problem_id))
    return True


async def _community(db: AsyncSession, problem_id: str) -> dict:
    problem = BY_ID[problem_id]
    stat = await db.get(ProblemCommunityStat, problem_id)
    if not stat:
        stat = ProblemCommunityStat(
            problem_id=problem_id, seeded_attempts=problem.seeded_attempts,
            seeded_solves=problem.seeded_solves,
            seeded_total_seconds=problem.seeded_solves * problem.seeded_average_seconds,
            seeded_fastest_seconds=problem.seeded_fastest_seconds,
        )
        db.add(stat)
        await db.flush()
    attempts = stat.real_attempts
    solves = stat.real_solves
    total_seconds = stat.real_total_seconds
    fastest_values = [v for v in (stat.real_fastest_seconds,) if v is not None]
    return {"attempts": attempts, "successful_solves": solves,
            "success_rate": round((solves / attempts * 100) if attempts else 0, 1),
            "average_solve_seconds": round(total_seconds / solves) if solves else None,
            "fastest_solve_seconds": min(fastest_values) if fastest_values else None,
            "real_attempts": stat.real_attempts}


def _profile_json(profile: ArenaProfile) -> dict:
    accuracy = round(profile.solved_count / profile.attempted_count * 100, 1) if profile.attempted_count else 0
    average = round(profile.total_solve_seconds / profile.solved_count) if profile.solved_count else None
    return {"arena_points": profile.points, "problems_solved": profile.solved_count,
            "attempted": profile.attempted_count, "accuracy": accuracy,
            "average_solve_seconds": average, "head_to_head_wins": profile.h2h_wins,
            "attack_best_streak": profile.attack_best_streak}


def _battle_json(battle: CodingBattle, user_id: uuid.UUID) -> dict:
    opponent_alias = battle.player_two_alias if user_id == battle.player_one_id else battle.player_one_alias
    return {"id": str(battle.id), "kind": battle.kind, "room_code": battle.room_code,
            "language": battle.language, "difficulty": battle.difficulty, "topic": battle.topic,
            "problem_id": battle.problem_id, "status": battle.status.value,
            "opponent_alias": opponent_alias, "winner_id": str(battle.winner_id) if battle.winner_id else None,
            "winner_seconds": battle.winner_seconds,
            "started_at": battle.started_at.isoformat() if battle.started_at else None}


@router.get("/config")
async def config():
    from app.config import settings
    return {"languages": [{"id": "python", "label": "Python 3"}, {"id": "cpp", "label": "C++17"}, {"id": "java", "label": "Java"}],
            "difficulties": ["easy", "medium", "hard"], "topics": ["arrays", "strings", "searching", "sorting"],
            "execution_provider": "judge0" if settings.JUDGE0_URL else "safe_demo",
            "execution_available": bool(settings.JUDGE0_URL)}


@router.get("/profile")
async def profile(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    value = await _profile(db, current_user.id)
    tx = (await db.execute(select(ArenaTransaction).where(ArenaTransaction.user_id == current_user.id)
        .order_by(ArenaTransaction.created_at.desc()).limit(12))).scalars().all()
    await db.commit()
    return {**_profile_json(value), "transactions": [{"amount": t.amount, "reason": t.reason,
        "problem_id": t.problem_id, "created_at": t.created_at.isoformat()} for t in tx]}


@router.get("/history")
async def history(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    submissions = (await db.execute(select(CodingSubmission).where(CodingSubmission.user_id == current_user.id)
        .order_by(CodingSubmission.created_at.desc()).limit(30))).scalars().all()
    attacks = (await db.execute(select(AttackSession).where(AttackSession.user_id == current_user.id, AttackSession.active == False)
        .order_by(AttackSession.ended_at.desc()).limit(10))).scalars().all()
    return {"submissions": [{"id": str(s.id), "problem_id": s.problem_id, "title": BY_ID[s.problem_id].title,
        "mode": s.mode, "language": s.language, "accepted": s.accepted, "passed_tests": s.passed_tests,
        "total_tests": s.total_tests, "solve_seconds": s.solve_seconds, "created_at": s.created_at.isoformat()} for s in submissions],
        "attack_sessions": [{"id": str(a.id), "attempted": a.attempted, "solved": a.solved,
        "best_streak": a.best_streak, "points_earned": a.points_earned,
        "total_seconds": a.total_seconds, "ended_at": a.ended_at.isoformat() if a.ended_at else None} for a in attacks]}


@router.get("/problems")
async def problems(language: str = Query("python"), difficulty: str | None = None, topic: str | None = None):
    if language not in {"python", "cpp", "java"}: raise HTTPException(422, "Unsupported language")
    values = [p for p in PROBLEMS if (not difficulty or p.difficulty == difficulty) and (not topic or p.topic == topic)]
    return {"problems": [p.public(language) for p in values]}


@router.get("/problems/{problem_id}")
async def problem(problem_id: str, language: str = Query("python"), current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if problem_id not in BY_ID or language not in {"python", "cpp", "java"}: raise HTTPException(404, "Problem not found")
    unlocked = (await db.execute(select(HintUnlock.hint_index).where(HintUnlock.user_id == current_user.id,
        HintUnlock.problem_id == problem_id).order_by(HintUnlock.hint_index))).scalars().all()
    community = await _community(db, problem_id)
    await db.commit()
    value = BY_ID[problem_id].public(language)
    value["unlocked_hints"] = [{"index": i, "text": BY_ID[problem_id].hints[i]} for i in unlocked if i < len(BY_ID[problem_id].hints)]
    value["community"] = community
    return value


@router.post("/run")
async def run_code(request: RunRequest, current_user=Depends(get_current_user)):
    if request.problem_id not in BY_ID: raise HTTPException(404, "Problem not found")
    result = await get_execution_provider().execute(request.language, request.source_code, request.stdin)
    return result.json()


@router.post("/hints/unlock")
async def unlock_hint(request: HintRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    problem = BY_ID.get(request.problem_id)
    if not problem or request.hint_index >= len(problem.hints): raise HTTPException(404, "Hint not found")
    existing = await db.scalar(select(HintUnlock.id).where(HintUnlock.user_id == current_user.id,
        HintUnlock.problem_id == request.problem_id, HintUnlock.hint_index == request.hint_index))
    profile = await _profile(db, current_user.id)
    if existing:
        return {"charged": False, "hint": problem.hints[request.hint_index], "arena_points": profile.points}
    if request.hint_index:
        unlocked_count = await db.scalar(select(func.count(HintUnlock.id)).where(
            HintUnlock.user_id == current_user.id, HintUnlock.problem_id == request.problem_id,
            HintUnlock.hint_index < request.hint_index))
        if unlocked_count != request.hint_index:
            raise HTTPException(409, "Hints must be unlocked in order")
    await _add_points(db, profile, -50, "HINT", f"hint:{request.problem_id}:{request.hint_index}", request.problem_id)
    db.add(HintUnlock(user_id=current_user.id, problem_id=request.problem_id, hint_index=request.hint_index))
    if request.attack_session_id:
        try:
            attack = await db.get(AttackSession, uuid.UUID(request.attack_session_id))
            if attack and attack.user_id == current_user.id and attack.active: attack.hints_used += 1
        except ValueError: pass
    await db.commit()
    return {"charged": True, "hint": problem.hints[request.hint_index], "arena_points": profile.points}


@router.post("/submit")
async def submit(request: SubmitRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    problem = BY_ID.get(request.problem_id)
    if not problem: raise HTTPException(404, "Problem not found")
    solve_seconds = request.solve_seconds
    battle = None
    if request.mode in {"head_to_head", "friend"}:
        try: battle = await db.get(CodingBattle, uuid.UUID(request.session_id or ""))
        except ValueError: battle = None
        if not battle or current_user.id not in {battle.player_one_id, battle.player_two_id}:
            raise HTTPException(404, "Battle not found")
        if battle.status != BattleStatus.ACTIVE:
            raise HTTPException(409, "Battle is already complete")
        if request.problem_id != battle.problem_id or request.language != battle.language:
            raise HTTPException(409, "Submission does not match this battle")
        if battle.started_at:
            started_at = battle.started_at if battle.started_at.tzinfo else battle.started_at.replace(tzinfo=timezone.utc)
            solve_seconds = max(1, int((datetime.now(timezone.utc) - started_at).total_seconds()))
    provider = get_execution_provider()
    passed = 0; failure = None; total = len(problem.hidden_tests)
    for test in problem.hidden_tests:
        result = await provider.execute(request.language, request.source_code, test["input"])
        if not result.available:
            return {**result.json(), "accepted": False, "passed_tests": 0, "total_tests": total,
                    "message": "Execution is disabled until a sandbox provider is configured."}
        if result.status != "accepted":
            failure = result; break
        from app.services.problem_catalog import VALIDATORS
        if request.problem_id in VALIDATORS:
            is_match = VALIDATORS[request.problem_id](result.stdout, test)
        else:
            is_match = outputs_match(result.stdout, test["output"])
        if not is_match:
            failure = result; failure.status = "wrong_answer"; break
        passed += 1
    accepted = passed == total
    profile = await _profile(db, current_user.id)
    prior_accepted = await db.scalar(select(CodingSubmission.id).where(CodingSubmission.user_id == current_user.id,
        CodingSubmission.problem_id == request.problem_id, CodingSubmission.accepted == True).limit(1))
    submission = CodingSubmission(user_id=current_user.id, problem_id=request.problem_id, language=request.language,
        mode=request.mode, session_id=request.session_id, accepted=accepted, passed_tests=passed,
        total_tests=total, solve_seconds=solve_seconds if accepted else None,
        status="accepted" if accepted else (failure.status if failure else "wrong_answer"))
    db.add(submission)
    profile.attempted_count += 1
    awarded = 0
    if accepted and not prior_accepted:
        if await _add_points(db, profile, 100, "SOLVED", f"solved:{request.problem_id}", request.problem_id):
            awarded += 100; profile.solved_count += 1; profile.total_solve_seconds += solve_seconds
    stat = await db.get(ProblemCommunityStat, request.problem_id)
    if not stat:
        await _community(db, request.problem_id); stat = await db.get(ProblemCommunityStat, request.problem_id)
    stat.real_attempts += 1
    if accepted:
        stat.real_solves += 1; stat.real_total_seconds += solve_seconds
        stat.real_fastest_seconds = min(v for v in (stat.real_fastest_seconds, solve_seconds) if v is not None)

    next_problem = None; victory = False
    if request.mode == "attack" and request.session_id:
        try: attack = await db.get(AttackSession, uuid.UUID(request.session_id))
        except ValueError: attack = None
        if attack and attack.user_id == current_user.id and attack.active:
            prior_attack_solve = await db.scalar(select(CodingSubmission.id).where(
                CodingSubmission.user_id == current_user.id, CodingSubmission.session_id == request.session_id,
                CodingSubmission.problem_id == request.problem_id, CodingSubmission.accepted == True,
                CodingSubmission.id != submission.id).limit(1))
            attack.attempted += 1; attack.total_seconds += solve_seconds
            if accepted and not prior_attack_solve:
                attack.solved += 1; attack.current_streak += 1; attack.best_streak = max(attack.best_streak, attack.current_streak)
                attack.fastest_seconds = min(v for v in (attack.fastest_seconds, solve_seconds) if v is not None)
                attack.points_earned += awarded
            elif not accepted: attack.current_streak = 0
            profile.attack_best_streak = max(profile.attack_best_streak, attack.best_streak)
            next_problem = select_problem(attack.language, attack.difficulty, attack.topic, f"{attack.id}:{attack.attempted}").public(attack.language)
    if request.mode in {"head_to_head", "friend"} and request.session_id and accepted:
        if battle and battle.status == BattleStatus.ACTIVE and current_user.id in {battle.player_one_id, battle.player_two_id} and not battle.winner_id:
            battle.winner_id = current_user.id; battle.winner_seconds = solve_seconds
            battle.status = BattleStatus.COMPLETED; battle.completed_at = datetime.now(timezone.utc)
            if await _add_points(db, profile, 50, "VICTORY", f"victory:{battle.id}", request.problem_id):
                awarded += 50; victory = True; profile.h2h_wins += 1
    await db.commit()
    if victory and battle:
        from app.websockets.coding_ws import notify_battle_result
        await notify_battle_result(str(battle.id), str(current_user.id), solve_seconds)
    community = await _community(db, request.problem_id); await db.commit()
    average = community["average_solve_seconds"] or solve_seconds or 1
    faster_than = max(1, min(99, round(50 + (average - solve_seconds) / max(average, 1) * 45))) if accepted else 0
    return {"status": "accepted" if accepted else (failure.status if failure else "wrong_answer"),
        "accepted": accepted, "passed_tests": passed, "total_tests": total, "arena_points": profile.points,
        "points_awarded": awarded, "victory": victory, "community": community, "faster_than_percent": faster_than,
        "next_problem": next_problem, "solve_seconds": solve_seconds,
        "stderr": failure.stderr if failure else "", "compile_output": failure.compile_output if failure else ""}


@router.post("/attack/start")
async def attack_start(filters: ArenaFilters, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _profile(db, current_user.id)
    attack = AttackSession(user_id=current_user.id, **filters.model_dump())
    db.add(attack); await db.flush()
    problem = select_problem(filters.language, filters.difficulty, filters.topic, str(attack.id))
    await db.commit()
    return {"session_id": str(attack.id), "problem": problem.public(filters.language)}


@router.post("/attack/{session_id}/end")
async def attack_end(session_id: uuid.UUID, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    attack = await db.get(AttackSession, session_id)
    if not attack or attack.user_id != current_user.id: raise HTTPException(404, "Attack session not found")
    attack.active = False; attack.ended_at = datetime.now(timezone.utc); await db.commit()
    return {"attempted": attack.attempted, "solved": attack.solved,
        "accuracy": round(attack.solved / attack.attempted * 100, 1) if attack.attempted else 0,
        "average_solve_seconds": round(attack.total_seconds / attack.attempted) if attack.attempted else None,
        "fastest_solve_seconds": attack.fastest_seconds, "longest_streak": attack.best_streak,
        "hints_used": attack.hints_used, "points_earned": attack.points_earned, "total_seconds": attack.total_seconds}


def _code(): return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


@router.post("/battles/matchmake")
async def matchmake(filters: ArenaFilters, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    waiting = await db.scalar(select(CodingBattle).where(CodingBattle.kind == "head_to_head",
        CodingBattle.language == filters.language, CodingBattle.difficulty == filters.difficulty,
        CodingBattle.topic == filters.topic, CodingBattle.status == BattleStatus.WAITING,
        CodingBattle.player_one_id != current_user.id).order_by(CodingBattle.created_at).limit(1))
    now = datetime.now(timezone.utc)
    if waiting:
        waiting.player_two_id = current_user.id; waiting.player_two_alias = _alias(current_user)
        waiting.status = BattleStatus.ACTIVE; waiting.started_at = now; battle = waiting
    else:
        existing = await db.scalar(select(CodingBattle).where(CodingBattle.kind == "head_to_head",
            CodingBattle.player_one_id == current_user.id, CodingBattle.status == BattleStatus.WAITING).limit(1))
        if existing: battle = existing
        else:
            chosen = select_problem(filters.language, filters.difficulty, filters.topic, now.isoformat())
            battle = CodingBattle(kind="head_to_head", problem_id=chosen.id, player_one_id=current_user.id,
                player_one_alias=_alias(current_user), **filters.model_dump())
            db.add(battle); await db.flush()
    await db.commit()
    return _battle_json(battle, current_user.id)


@router.post("/battles/rooms")
async def create_room(filters: ArenaFilters, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    room = _code()
    while await db.scalar(select(CodingBattle.id).where(CodingBattle.room_code == room)): room = _code()
    chosen = select_problem(filters.language, filters.difficulty, filters.topic, room)
    battle = CodingBattle(kind="friend", room_code=room, problem_id=chosen.id,
        player_one_id=current_user.id, player_one_alias=_alias(current_user), **filters.model_dump())
    db.add(battle); await db.flush(); await db.commit()
    return _battle_json(battle, current_user.id)


@router.post("/battles/rooms/join")
async def join_room(request: JoinRoomRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    battle = await db.scalar(select(CodingBattle).where(CodingBattle.room_code == request.room_code.upper()).limit(1))
    if not battle: raise HTTPException(404, "Room not found")
    if battle.player_one_id == current_user.id: return _battle_json(battle, current_user.id)
    if battle.player_two_id and battle.player_two_id != current_user.id: raise HTTPException(409, "Room is full")
    if battle.status == BattleStatus.WAITING:
        battle.player_two_id = current_user.id; battle.player_two_alias = _alias(current_user)
        battle.status = BattleStatus.ACTIVE; battle.started_at = datetime.now(timezone.utc); await db.commit()
    return _battle_json(battle, current_user.id)


@router.get("/battles/{battle_id}")
async def battle_status(battle_id: uuid.UUID, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    battle = await db.get(CodingBattle, battle_id)
    if not battle or current_user.id not in {battle.player_one_id, battle.player_two_id}: raise HTTPException(404, "Battle not found")
    return _battle_json(battle, current_user.id)
