from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.db.session import init_db
from app.graph.checkpointer import checkpointer_context
from app.graph.graph import crear_grafo
from app.web.routes import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # El checkpointer se abre una vez, aqui, y se queda vivo mientras la app este
    # arriba -- el grafo lo necesita para poder pausar y reanudar en cualquier
    # request, no solo en la que lo crea.
    with checkpointer_context() as checkpointer:
        app.state.grafo = crear_grafo(checkpointer)
        yield


app = FastAPI(title="Agente de triaje de incidencias logísticas", lifespan=lifespan)
app.include_router(api_router)
app.include_router(web_router)
