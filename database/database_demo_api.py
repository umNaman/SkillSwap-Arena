from fastapi import FastAPI
from database import engine
from sqlalchemy import text

app = FastAPI(title="SkillSwap API")


@app.get("/")
def home():
    return {"message": "SkillSwap API is running"}


@app.get("/test-db")
def test_database():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))

            return {
                "database": "connected",
                "result": result.scalar()
            }

    except Exception as e:
        return {
            "database": "connection failed",
            "error": str(e)
        }


@app.get("/users")
def get_users():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT user_id, alias, avatar, created_at FROM users"
                )
            )

            users = []

            for row in result:
                users.append({
                    "user_id": row.user_id,
                    "alias": row.alias,
                    "avatar": row.avatar,
                    "created_at": str(row.created_at)
                })

            return users

    except Exception as e:
        return {"error": str(e)}


@app.get("/users/{user_id}/performance")
def get_performance(user_id: int):
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        u.alias AS student,
                        t.topic_text AS gd_topic,
                        g.status AS session_status,
                        a.communication_score,
                        a.confidence_score,
                        a.relevance_score,
                        a.participation_score,
                        a.leadership_score,
                        a.strengths,
                        a.weaknesses,
                        a.recommendation
                    FROM ai_feedback a
                    JOIN users u
                        ON a.user_id = u.user_id
                    JOIN gd_sessions g
                        ON a.session_id = g.session_id
                    JOIN topics t
                        ON g.topic_id = t.topic_id
                    WHERE u.user_id = :user_id
                """),
                {"user_id": user_id}
            ).mappings().first()

            if result is None:
                return {
                    "message": "No performance data found"
                }

            return dict(result)

    except Exception as e:
        return {
            "error": str(e)
        }        