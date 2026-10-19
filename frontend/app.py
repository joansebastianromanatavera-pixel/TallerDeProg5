"""GymFlow Streamlit front page. Run with: streamlit run frontend/app.py"""

import streamlit as st

import api_client

st.set_page_config(page_title="GymFlow", page_icon="🏋️", layout="wide")

st.title("🏋️ GymFlow")
st.markdown(
    """
Sistema de gestión de gimnasio con asistente de IA.

- **Socios**: crear, consultar, editar y eliminar socios (API REST con FastAPI).
- **Asistente IA**: preguntas de entrenamiento respondidas por Google Gemini con
  tres técnicas de prompting (zero-shot, few-shot y chain-of-thought) y RAG sobre los datos del gimnasio.

Usa el menú lateral para navegar entre las páginas.
"""
)

st.subheader("Estado de la API")
try:
    info = api_client.health()
    st.success(f"API en línea · versión {info.get('version', '?')} · {api_client.API_URL}")
    st.markdown(f"Documentación OpenAPI: [{api_client.API_URL}/docs]({api_client.API_URL}/docs)")
except api_client.APIError as exc:
    st.error(f"API no disponible: {exc}")
    st.code("uvicorn gymflow.api.main:app --reload", language="bash")
