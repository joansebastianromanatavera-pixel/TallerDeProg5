"""GymFlow FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import gymflow.models  # noqa: F401  (registers the tables on Base.metadata)
from gymflow.api.errors import register_error_handlers
from gymflow.api.routers import ai, members
from gymflow.db import Base, engine

API_VERSION = "1.0.0"

DESCRIPTION = """
**GymFlow API** manages the members of a gym and offers an AI fitness assistant.

* **Members**: full CRUD (create, list, read, update, delete) with robust HTTP error handling.
* **AI**: Google Gemini integration with three prompting techniques
  (zero-shot, few-shot, chain-of-thought) and basic RAG over the GymFlow database.

Every error uses the same JSON shape: `{"error": str, "detail": any, "status": int}`.
"""

TAGS_METADATA = [
    {"name": "Members", "description": "CRUD operations for gym members."},
    {"name": "AI", "description": "LLM-powered fitness assistant with prompt engineering and RAG."},
    {"name": "Health", "description": "Service status."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="GymFlow API",
    version=API_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(members.router)
app.include_router(ai.router)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns `ok` when the API is up and running.",
)
def health() -> dict[str, str]:
    return {"status": "ok", "version": API_VERSION}
