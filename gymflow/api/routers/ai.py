"""LLM assistant endpoint. The heavy lifting lives in gymflow.services."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gymflow.api.deps import get_db
from gymflow.api.schemas import AIRequest, AIResponse, ErrorOut
from gymflow.models import Socio
from gymflow.services import llm_service
from gymflow.services.prompts import build_prompt
from gymflow.services.rag import retrieve_context

router = APIRouter(prefix="/api/v1", tags=["AI"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/ai",
    response_model=AIResponse,
    summary="Ask the GymFlow AI assistant",
    description=(
        "Answers a fitness question with Google Gemini. The API retrieves context from the GymFlow "
        "database (basic RAG: member data, memberships, routines and keyword-matched exercises), "
        "builds a prompt with the selected technique (`zero_shot`, `few_shot` or `cot`) and returns "
        "the answer together with the sources used, token usage and latency."
    ),
    responses={
        200: {"description": "Answer generated."},
        404: {"model": ErrorOut, "description": "The given member_id does not exist."},
        422: {"model": ErrorOut, "description": "Invalid request body."},
        429: {"model": ErrorOut, "description": "LLM provider rate limit reached. Retry later."},
        503: {"model": ErrorOut, "description": "LLM provider unavailable or not configured."},
        504: {"model": ErrorOut, "description": "LLM provider did not answer in time."},
    },
)
def ask_ai(payload: AIRequest, db: DbSession) -> AIResponse:
    if payload.member_id is not None and db.get(Socio, payload.member_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member with id {payload.member_id} was not found.")

    context, sources = retrieve_context(db, payload.question, payload.member_id)
    prompt = build_prompt(payload.technique, payload.question, context)
    # Called through the module so tests can monkeypatch llm_service.ask_llm.
    result = llm_service.ask_llm(prompt, technique=payload.technique)

    return AIResponse(
        answer=result.text,
        technique=payload.technique,
        sources=sources,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
    )
