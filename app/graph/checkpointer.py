"""El checkpointer es lo que permite que interrupt() pause el grafo de verdad:
sin el, el estado no sobrevive entre el invoke que se pausa y el que reanuda.

En produccion (docker-compose) usamos Postgres. En local, sin Postgres instalado,
cae a un fichero SQLite para poder desarrollar y correr los tests sin infraestructura.
"""

from contextlib import contextmanager

from app.config import settings


@contextmanager
def checkpointer_context():
    if settings.postgres_dsn:
        from langgraph.checkpoint.postgres import PostgresSaver

        with PostgresSaver.from_conn_string(settings.postgres_dsn) as saver:
            saver.setup()
            yield saver
    else:
        from langgraph.checkpoint.sqlite import SqliteSaver

        with SqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
            saver.setup()
            yield saver
