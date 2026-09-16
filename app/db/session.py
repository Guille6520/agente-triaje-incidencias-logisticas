from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.models import Base, Pedido

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

PEDIDOS_DE_PRUEBA = [
    Pedido(numero_pedido="45231", titular_email="carlos.lopez@mercadona.es", transportista="TransIberia", valor=1250.0, estado="en_transito", tiene_foto=False),
    Pedido(numero_pedido="89104", titular_email="almacen@techparts.com", transportista="RapidExpress", valor=2400.0, estado="entregado", tiene_foto=True),
    Pedido(numero_pedido="12445", titular_email="logistica@fashionstore.es", transportista="MensajerosNorte", valor=320.0, estado="entregado", tiene_foto=False),
    Pedido(numero_pedido="54321", titular_email="cliente.real@gmail.com", transportista="MensajerosNorte", valor=200.0, estado="en_transito", tiene_foto=False),
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Pedido).count() == 0:
            db.add_all(PEDIDOS_DE_PRUEBA)
            db.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
