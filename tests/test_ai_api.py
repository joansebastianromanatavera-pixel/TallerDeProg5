"""Tests for the AI endpoint. The LLM is always mocked: the real API is never called."""

from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from gymflow.services import llm_service
from gymflow.services.llm_service import LLMResult


def test_ask_ai_returns_ai_response(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_ask_llm(prompt: str, technique: str = "unknown") -> LLMResult:
        captured["prompt"] = prompt
        return LLMResult(text="Rest 2-3 days per week.", input_tokens=120, output_tokens=15, latency_ms=42)

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/api/v1/ai", json={"question": "How many rest days do I need?", "technique": "cot"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Rest 2-3 days per week.",
        "technique": "cot",
        "sources": [],
        "input_tokens": 120,
        "output_tokens": 15,
        "latency_ms": 42,
    }
    assert "Think step by step" in captured["prompt"]


def test_ask_ai_timeout_returns_504(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ask_llm(prompt: str, technique: str = "unknown") -> LLMResult:
        raise HTTPException(504, "The LLM provider did not answer in time.")

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post("/api/v1/ai", json={"question": "Best chest exercise?", "technique": "zero_shot"})

    assert response.status_code == 504
    assert response.json()["error"] == "Gateway Timeout"
    assert response.json()["status"] == 504


def test_llm_service_maps_provider_timeout_to_504(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ask_llm itself turns a provider timeout into HTTP 504 (fake client, no network)."""

    class FakeModels:
        def generate_content(self, **kwargs: object) -> None:
            raise httpx.ReadTimeout("timed out")

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(llm_service.genai, "Client", FakeClient)
    monkeypatch.setattr(llm_service, "LOG_PATH", tmp_path / "llm_calls.jsonl")

    with pytest.raises(HTTPException) as exc_info:
        llm_service.ask_llm("hello", technique="zero_shot")

    assert exc_info.value.status_code == 504
    assert '"status": 504' in (tmp_path / "llm_calls.jsonl").read_text(encoding="utf-8")
