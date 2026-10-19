# GymFlow

Sistema de gestión de gimnasio: API REST con **FastAPI** (CRUD de socios + asistente de IA con **Google Gemini**) y frontend en **Streamlit**.
Guía 5 de Taller de Programación: APIs REST modernas e integración de LLMs.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Streamlit · pytest · google-genai

## Instalación

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # luego pon tu GEMINI_API_KEY en .env
```

Variables de entorno (`.env`):

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de SQLAlchemy (por defecto `sqlite:///./gymflow.db`) |
| `GEMINI_API_KEY` | API key de Google AI Studio (nunca se sube al repositorio) |
| `GEMINI_MODEL` | Modelo de Gemini; si se deja vacío se usa `gemini-2.5-flash` |
| `API_URL` | URL de la API que usa el frontend (`http://localhost:8000`) |
| `LLM_TIMEOUT_SECONDS` | Timeout de cada llamada al LLM (por defecto 15) |

Datos de prueba (opcional):

```bash
python -m gymflow.seed
```

## Ejecutar la API

```bash
uvicorn gymflow.api.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health

### Endpoints

| Método | Ruta | Respuestas |
|---|---|---|
| POST | `/api/v1/members` | 201, 409, 422 |
| GET | `/api/v1/members?skip=0&limit=20` | 200 |
| GET | `/api/v1/members/{id}` | 200, 404 |
| PUT | `/api/v1/members/{id}` | 200, 404, 409, 422 |
| DELETE | `/api/v1/members/{id}` | 204, 404 |
| POST | `/api/v1/ai` | 200, 404, 422, 429, 503, 504 |

Todos los errores tienen el formato `{"error": str, "detail": any, "status": int}`.
Cada llamada al LLM queda registrada en `logs/llm_calls.jsonl`, que está ignorado en git.

## Ejecutar el frontend

Con la API corriendo, en otra terminal:

```bash
streamlit run frontend/app.py
```

Se abre en http://localhost:8501 con las páginas **Socios** y **Asistente IA**.

## Tests

```bash
pytest -v
```

Los tests usan SQLite en memoria y el LLM mockeado, así que no necesitan API key ni red. El pipeline de GitHub Actions (`.github/workflows/ci.yml`) los ejecuta en cada push y PR a `main`.

## Estructura

```
gymflow/
├── db.py              # engine, SessionLocal, Base
├── seed.py            # datos semilla opcionales
├── models/            # Socio, Membresia, Rutina, Ejercicio
├── api/               # main, deps, schemas, errors, routers/{members, ai}
└── services/          # llm_service, prompts (zero-shot/few-shot/CoT), rag
frontend/              # app.py, api_client.py, pages/
tests/                 # conftest, test_members_api, test_ai_api
```
