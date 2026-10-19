"""AI assistant page: ask Gemini with zero-shot, few-shot or chain-of-thought prompting."""

from typing import Any

import streamlit as st

import api_client

st.set_page_config(page_title="Asistente IA · GymFlow", page_icon="🤖", layout="wide")
st.title("🤖 Asistente IA")
st.caption("Respuestas de Google Gemini con contexto recuperado de la base de datos de GymFlow (RAG).")

TECHNIQUES = {"zero_shot": "Zero-shot", "few_shot": "Few-shot", "cot": "Chain-of-Thought"}


def show_answer(result: dict[str, Any]) -> None:
    st.markdown(result["answer"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Tokens entrada", result["input_tokens"])
    c2.metric("Tokens salida", result["output_tokens"])
    c3.metric("Latencia", f"{result['latency_ms']} ms")
    st.caption("Fuentes: " + (", ".join(result["sources"]) if result["sources"] else "ninguna"))


try:
    members = api_client.list_members()
except api_client.APIError as exc:
    st.error(str(exc))
    st.stop()

member_options: list[dict[str, Any] | None] = [None, *members]

question = st.text_area(
    "Pregunta", placeholder="Ej.: ¿Qué ejercicios de mi rutina trabajan el pecho?", height=100
)
col_tech, col_member = st.columns(2)
technique = col_tech.selectbox("Técnica de prompting", list(TECHNIQUES), format_func=TECHNIQUES.get)
member = col_member.selectbox(
    "Socio (contexto RAG)",
    member_options,
    format_func=lambda m: "Sin socio (consulta general)" if m is None else f"#{m['id']} · {m['name']}",
)
member_id = member["id"] if member else None

col_ask, col_compare = st.columns([1, 1])
ask_clicked = col_ask.button("Preguntar", type="primary", width="stretch")
compare_clicked = col_compare.button("Comparar 3 técnicas", width="stretch")

if (ask_clicked or compare_clicked) and len(question.strip()) < 3:
    st.error("Escribe una pregunta de al menos 3 caracteres.")
    st.stop()

if ask_clicked:
    with st.spinner(f"Consultando con {TECHNIQUES[technique]}..."):
        try:
            show_answer(api_client.ask_ai(question, technique, member_id))
        except api_client.APIError as exc:
            st.error(str(exc))

if compare_clicked:
    columns = st.columns(3)
    for col, (key, label) in zip(columns, TECHNIQUES.items()):
        with col:
            st.subheader(label)
            with st.spinner("Consultando..."):
                try:
                    show_answer(api_client.ask_ai(question, key, member_id))
                except api_client.APIError as exc:
                    st.error(str(exc))
