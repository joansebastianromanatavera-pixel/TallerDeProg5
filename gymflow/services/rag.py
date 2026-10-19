"""Basic RAG: retrieve relevant GymFlow records to ground the LLM answer."""

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from gymflow.models import Ejercicio, Rutina, Socio

TOP_K_EXERCISES = 5
NO_CONTEXT = "No relevant data found in the GymFlow database."

STOPWORDS = {
    # español
    "para", "como", "cómo", "cual", "cuál", "cuales", "cuáles", "que", "qué", "este", "esta",
    "estos", "estas", "tengo", "puedo", "debo", "hacer", "sobre", "entre", "desde", "hasta",
    "mejor", "mejores", "rutina", "ejercicio", "ejercicios", "quiero", "cuando", "cuándo",
    "donde", "dónde", "porque", "tiene", "tienen", "mucho", "muchos", "algún", "alguna",
    # english
    "what", "which", "where", "when", "with", "that", "this", "these", "have", "does", "should",
    "could", "would", "about", "from", "your", "mine", "best", "routine", "exercise", "exercises",
}


def _keywords(question: str) -> list[str]:
    words = re.findall(r"\w+", question.lower())
    return list(dict.fromkeys(w for w in words if len(w) >= 4 and w not in STOPWORDS))


def _describe_exercise(ex: Ejercicio) -> str:
    text = f"{ex.nombre} {ex.series}x{ex.repeticiones} (muscle group: {ex.grupo_muscular})"
    return f"{text}: {ex.descripcion.rstrip('.')}" if ex.descripcion else text


def _member_context(db: Session, member_id: int) -> tuple[list[str], list[str], set[int]]:
    socio = db.scalar(
        select(Socio)
        .where(Socio.id == member_id)
        .options(
            selectinload(Socio.membresias),
            selectinload(Socio.rutinas).selectinload(Rutina.ejercicios),
        )
    )
    if socio is None:
        return [], [], set()

    lines = [
        f"Member: {socio.nombre} (id {socio.id}), registered on {socio.fecha_registro}, "
        f"status: {'active' if socio.activo else 'inactive'}."
    ]
    sources = [f"member:{socio.id}"]
    seen_exercises: set[int] = set()

    for m in socio.membresias:
        lines.append(
            f"Membership: {m.tipo}, from {m.fecha_inicio} to {m.fecha_fin}, price {m.precio}, "
            f"{'active' if m.activa else 'inactive'}."
        )
        sources.append(f"membership:{m.id}")

    for r in socio.rutinas:
        exercises = "; ".join(_describe_exercise(ex) for ex in r.ejercicios) or "no exercises"
        lines.append(f"Routine '{r.nombre}' (goal: {r.objetivo}, level: {r.nivel}): {exercises}.")
        sources.append(f"routine:{r.id}")
        seen_exercises.update(ex.id for ex in r.ejercicios)

    return lines, sources, seen_exercises


def _keyword_exercises(db: Session, question: str, exclude: set[int]) -> list[Ejercicio]:
    keywords = _keywords(question)
    if not keywords:
        return []

    filters = [
        column.ilike(f"%{kw}%")
        for kw in keywords
        for column in (Ejercicio.nombre, Ejercicio.grupo_muscular, Ejercicio.descripcion)
    ]
    candidates = [ex for ex in db.scalars(select(Ejercicio).where(or_(*filters)).limit(100)) if ex.id not in exclude]

    def score(ex: Ejercicio) -> int:
        haystack = f"{ex.nombre} {ex.grupo_muscular} {ex.descripcion or ''}".lower()
        return sum(kw in haystack for kw in keywords)

    candidates.sort(key=score, reverse=True)
    return candidates[:TOP_K_EXERCISES]


def retrieve_context(db: Session, question: str, member_id: int | None) -> tuple[str, list[str]]:
    """Return (context_text, sources) for the question, optionally personalised for a member."""
    lines: list[str] = []
    sources: list[str] = []
    seen_exercises: set[int] = set()

    if member_id is not None:
        lines, sources, seen_exercises = _member_context(db, member_id)

    related = _keyword_exercises(db, question, seen_exercises)
    if related:
        lines.append("Related exercises in the GymFlow catalog:")
        lines.extend(f"- {_describe_exercise(ex)}" for ex in related)
        sources.extend(f"exercise:{ex.id}" for ex in related)

    return ("\n".join(lines) if lines else NO_CONTEXT), sources
