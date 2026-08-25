"""Sandboxed code execution abstraction for Coding Arena."""
import asyncio
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict

import httpx

from app.config import settings


LANGUAGE_IDS = {"python": 71, "cpp": 54, "java": 62}


@dataclass
class ExecutionResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    time: float | None = None
    available: bool = True

    def json(self) -> dict:
        return asdict(self)


class CodeExecutionProvider(ABC):
    @abstractmethod
    async def execute(self, language: str, source: str, stdin: str) -> ExecutionResult:
        raise NotImplementedError


class Judge0ExecutionProvider(CodeExecutionProvider):
    """Judge0 CE-compatible remote sandbox. User code never runs in FastAPI."""
    def __init__(self, base_url: str, api_key: str = "", api_host: str = ""):
        self.base_url = base_url.rstrip("/")
        self.headers = {"content-type": "application/json"}
        if api_key:
            self.headers["X-RapidAPI-Key"] = api_key
        if api_host:
            self.headers["X-RapidAPI-Host"] = api_host

    @staticmethod
    def _encode(value: str) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("ascii")

    @staticmethod
    def _decode(value: str | None) -> str:
        if not value:
            return ""
        return base64.b64decode(value).decode("utf-8", errors="replace")

    async def execute(self, language: str, source: str, stdin: str) -> ExecutionResult:
        if language not in LANGUAGE_IDS:
            return ExecutionResult("invalid_language", stderr="Unsupported language")
        payload = {"source_code": self._encode(source), "language_id": LANGUAGE_IDS[language], "stdin": self._encode(stdin),
                   "cpu_time_limit": 3, "wall_time_limit": 6, "memory_limit": 128000}
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                created = await client.post(f"{self.base_url}/submissions?base64_encoded=true&wait=false",
                                            headers=self.headers, json=payload)
                created.raise_for_status()
                token = created.json()["token"]
                data = None
                for _ in range(settings.JUDGE0_POLL_ATTEMPTS):
                    response = await client.get(
                        f"{self.base_url}/submissions/{token}?base64_encoded=true&fields=status,stdout,stderr,compile_output,time",
                        headers=self.headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                    if int(data.get("status", {}).get("id", 0)) > 2:
                        break
                    await asyncio.sleep(settings.JUDGE0_POLL_INTERVAL_MS / 1000)
                if not data or int(data.get("status", {}).get("id", 0)) <= 2:
                    return ExecutionResult("timeout", stderr="Execution provider timed out")
                status_id = int(data["status"]["id"])
                status = {3: "accepted", 4: "wrong_answer", 5: "time_limit", 6: "compile_error"}.get(status_id, "runtime_error")
                return ExecutionResult(status, self._decode(data.get("stdout")), self._decode(data.get("stderr")),
                                       self._decode(data.get("compile_output")), float(data["time"]) if data.get("time") else None)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return ExecutionResult("provider_error", stderr=f"Judge0 unavailable: {type(exc).__name__}", available=False)


class SafeDemoExecutionProvider(CodeExecutionProvider):
    """Non-executing fallback: explicit and safe, never pretends to compile code."""
    async def execute(self, language: str, source: str, stdin: str) -> ExecutionResult:
        return ExecutionResult(
            "execution_unavailable",
            stderr="Safe demo mode: configure JUDGE0_URL to compile and run code. No user code was executed.",
            available=False,
        )


def get_execution_provider() -> CodeExecutionProvider:
    if settings.JUDGE0_URL:
        return Judge0ExecutionProvider(settings.JUDGE0_URL, settings.JUDGE0_API_KEY, settings.JUDGE0_API_HOST)
    return SafeDemoExecutionProvider()


def outputs_match(actual: str, expected: str) -> bool:
    clean = lambda value: "\n".join(line.rstrip() for line in value.strip().splitlines())
    return clean(actual) == clean(expected)
