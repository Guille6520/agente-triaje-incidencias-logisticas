import os

# Hay que fijar esto ANTES de que nada importe app.config, porque Settings()
# se instancia una sola vez al importar el modulo.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_triaje.db")
os.environ.setdefault("GROQ_API_KEY", os.environ.get("GROQ_API_KEY") or "dummy-para-tests")
os.environ.setdefault("POSTGRES_DSN", "")

import pytest  # noqa: E402

from app.db.session import init_db  # noqa: E402

TIENE_GROQ_REAL = os.environ["GROQ_API_KEY"] not in ("", "dummy-para-tests", "dummy")

requiere_groq = pytest.mark.skipif(
    not TIENE_GROQ_REAL,
    reason="Requiere una GROQ_API_KEY real para probar los nodos que llaman al LLM",
)


@pytest.fixture(scope="session", autouse=True)
def _base_de_datos():
    init_db()
    yield


@pytest.fixture
def grafo():
    from langgraph.checkpoint.memory import MemorySaver

    from app.graph.graph import crear_grafo

    return crear_grafo(MemorySaver())
