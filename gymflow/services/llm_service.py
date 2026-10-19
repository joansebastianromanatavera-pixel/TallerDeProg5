"""Google Gemini client with timeout, one retry on rate limit, HTTP error mapping and JSONL logging."""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 2  # first try + 1 retry on 429
BACKOFF_SECONDS = 2.0
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "llm_calls.jsonl"

logger = logging.getLogger("gymflow.llm")


@dataclass(frozen=True)
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _log_call(record: dict[str, Any]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("Could not write LLM log to %s", LOG_PATH)


def _timeout_seconds() -> float:
    try:
        return float(os.getenv("LLM_TIMEOUT_SECONDS", "15"))
    except ValueError:
        return 15.0


def _call_gemini(client: genai.Client, model: str, prompt: str) -> types.GenerateContentResponse:
    """Call Gemini, retrying once with backoff on 429, and map failures to HTTPException."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise HTTPException(
                status.HTTP_504_GATEWAY_TIMEOUT, "The LLM provider did not answer in time."
            ) from exc
        except genai_errors.APIError as exc:
            if exc.code == 429:
                if attempt < MAX_ATTEMPTS:
                    time.sleep(BACKOFF_SECONDS * attempt)
                    continue
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "The LLM provider rate limit was reached. Please retry in a minute.",
                    headers={"Retry-After": "60"},
                ) from exc
            if exc.code in (408, 504):
                raise HTTPException(
                    status.HTTP_504_GATEWAY_TIMEOUT, "The LLM provider did not answer in time."
                ) from exc
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, f"The LLM provider returned an error ({exc.code})."
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Could not connect to the LLM provider."
            ) from exc
    raise AssertionError("unreachable")


def ask_llm(prompt: str, technique: str = "unknown") -> LLMResult:
    """Send the prompt to Gemini and return the answer, token usage and latency.

    Raises HTTPException 504 (timeout), 429 (rate limit) or 503 (missing key / provider error).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "technique": technique,
        "model": model,
        "prompt": prompt,
    }
    start = time.perf_counter()
    try:
        if not api_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "The LLM provider is not configured: GEMINI_API_KEY is missing.",
            )
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(_timeout_seconds() * 1000)),
        )
        response = _call_gemini(client, model, prompt)
        text = (response.text or "").strip()
        if not text:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "The LLM provider returned an empty answer."
            )
        usage = response.usage_metadata
        input_tokens = (usage.prompt_token_count or 0) if usage else 0
        # Thinking tokens are billed as output tokens, so they are included here.
        output_tokens = ((usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)) if usage else 0
        latency_ms = round((time.perf_counter() - start) * 1000)
        record.update(answer=text, input_tokens=input_tokens, output_tokens=output_tokens, latency_ms=latency_ms)
        return LLMResult(text, input_tokens, output_tokens, latency_ms)
    except HTTPException as exc:
        record.update(
            error=exc.detail, status=exc.status_code, latency_ms=round((time.perf_counter() - start) * 1000)
        )
        raise
    finally:
        _log_call(record)
