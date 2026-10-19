"""HTTP client for the GymFlow API used by the Streamlit pages."""

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
BASE_URL = f"{API_URL}/api/v1"
DEFAULT_TIMEOUT = 10
AI_TIMEOUT = 60  # LLM timeout + one retry with backoff


class APIError(Exception):
    """Raised when the API answers with an error (message taken from ErrorOut)."""

    def __init__(self, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:200]}"
    detail = body.get("detail", body)
    if isinstance(detail, list):  # validation errors: [{"field", "message"}]
        detail = "; ".join(f"{d.get('field', '')}: {d.get('message', d)}" for d in detail)
    return f"{body.get('error', 'Error')} ({response.status_code}): {detail}"


def _request(method: str, url: str, timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.Timeout as exc:
        raise APIError("The API took too long to respond.") from exc
    except requests.RequestException as exc:
        raise APIError(f"Cannot reach the API at {API_URL}. Is it running?") from exc
    if response.status_code >= 400:
        raise APIError(_error_message(response), response.status_code)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def health() -> dict[str, Any]:
    return _request("GET", f"{API_URL}/health", timeout=3)


def list_members(skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
    return _request("GET", f"{BASE_URL}/members", params={"skip": skip, "limit": limit})


def get_member(member_id: int) -> dict[str, Any]:
    return _request("GET", f"{BASE_URL}/members/{member_id}")


def create_member(data: dict[str, Any]) -> dict[str, Any]:
    return _request("POST", f"{BASE_URL}/members", json=data)


def update_member(member_id: int, data: dict[str, Any]) -> dict[str, Any]:
    return _request("PUT", f"{BASE_URL}/members/{member_id}", json=data)


def delete_member(member_id: int) -> None:
    _request("DELETE", f"{BASE_URL}/members/{member_id}")


def ask_ai(question: str, technique: str, member_id: int | None = None) -> dict[str, Any]:
    payload = {"question": question, "technique": technique, "member_id": member_id}
    return _request("POST", f"{BASE_URL}/ai", json=payload, timeout=AI_TIMEOUT)
