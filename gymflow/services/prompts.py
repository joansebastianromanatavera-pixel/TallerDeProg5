"""Prompt templates for the three prompting techniques: zero-shot, few-shot and chain-of-thought."""

from typing import Literal

Technique = Literal["zero_shot", "few_shot", "cot"]

SYSTEM_INSTRUCTIONS = (
    "You are GymFlow Assistant, a fitness assistant for a gym management system. "
    "Answer using the GymFlow context below when it is relevant. If the context does not contain "
    "the information needed, say so and give general, safe fitness advice. Never invent member data. "
    "Do not give medical diagnoses. Answer in the same language as the question, concisely."
)

FEW_SHOT_EXAMPLES: list[tuple[str, str, str]] = [
    (
        "Member: Carlos Ruiz. Routine 'Fuerza tren superior' (intermedio): "
        "Press de banca 4x8 (pecho), Remo con barra 4x10 (espalda).",
        "Which exercise in my routine works the chest?",
        "Your routine 'Fuerza tren superior' trains the chest with Press de banca: 4 sets of 8 reps.",
    ),
    (
        "Member: Ana Torres. Membership: mensual, from 2026-10-01 to 2026-10-31, active.",
        "¿Cuándo vence mi membresía?",
        "Tu membresía mensual vence el 2026-10-31. Renuévala antes de esa fecha para no perder el acceso.",
    ),
    (
        "No relevant data found in the GymFlow database.",
        "How many rest days per week does a beginner need?",
        "GymFlow has no specific data for this, but as general advice a beginner should rest 2-3 days "
        "per week, avoiding training the same muscle group on consecutive days.",
    ),
]


def _zero_shot(question: str, context: str) -> str:
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"### GymFlow context\n{context}\n\n"
        f"### Question\n{question}\n\n"
        "### Answer\n"
    )


def _few_shot(question: str, context: str) -> str:
    examples = "\n\n".join(
        f"Context: {ex_context}\nQuestion: {ex_question}\nAnswer: {ex_answer}"
        for ex_context, ex_question, ex_answer in FEW_SHOT_EXAMPLES
    )
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        "Follow the style of these examples: short, specific and grounded in the context.\n\n"
        f"### Examples\n{examples}\n\n"
        f"### Now answer\nContext: {context}\nQuestion: {question}\nAnswer:"
    )


def _chain_of_thought(question: str, context: str) -> str:
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"### GymFlow context\n{context}\n\n"
        f"### Question\n{question}\n\n"
        "Think step by step, then give the final answer. Use this format:\n"
        "Reasoning:\n1. ...\n2. ...\n"
        "Final answer: ..."
    )


_BUILDERS = {"zero_shot": _zero_shot, "few_shot": _few_shot, "cot": _chain_of_thought}


def build_prompt(technique: Technique, question: str, context: str) -> str:
    """Build the full prompt for the given technique."""
    try:
        builder = _BUILDERS[technique]
    except KeyError as exc:
        raise ValueError(f"Unknown prompting technique: {technique!r}") from exc
    return builder(question.strip(), context.strip())
