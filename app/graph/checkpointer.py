"""Sin checkpointer, interrupt() no sirve de nada: el estado no sobrevive entre
el invoke que pausa y el que reanuda, asi que esto es lo que hace posible la
pausa de verdad.

En produccion (docker-compose) es Postgres. En local, si no tienes Postgres
instalado, cae a un fichero SQLite -- asi puedo desarrollar y correr los tests
sin montar infraestructura.
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
