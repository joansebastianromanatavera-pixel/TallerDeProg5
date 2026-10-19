"""FastAPI dependencies."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from gymflow.db import SessionLocal


def get_db() -> Iterator[Session]:
    """Yield a database session and always close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
