import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Pedido(Base):
    """La tabla contra la que se contrasta cada incidencia (capa 'enriquecer')."""

    __tablename__ = "pedidos"

    numero_pedido: Mapped[str] = mapped_column(String, primary_key=True)
    titular_email: Mapped[str] = mapped_column(String)
    transportista: Mapped[str] = mapped_column(String)
    valor: Mapped[float] = mapped_column(Float)
    estado: Mapped[str] = mapped_column(String)
    tiene_foto: Mapped[bool] = mapped_column(Boolean)


class Incidencia(Base):
    """El registro de cada mensaje procesado. thread_id enlaza con el checkpoint de LangGraph."""

    __tablename__ = "incidencias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    email_id: Mapped[str] = mapped_column(String)
    remitente: Mapped[str] = mapped_column(String)
    asunto: Mapped[str | None] = mapped_column(String, nullable=True)
    cuerpo_mensaje: Mapped[str] = mapped_column(Text)

    tipo_incidencia: Mapped[str | None] = mapped_column(String, nullable=True)
    urgencia: Mapped[str | None] = mapped_column(String, nullable=True)
    resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_pedido: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    sospechoso: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    discrepancia: Mapped[str | None] = mapped_column(Text, nullable=True)

    motivo_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_verificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    respuesta_borrador: Mapped[str | None] = mapped_column(Text, nullable=True)
    respuesta_final: Mapped[str | None] = mapped_column(Text, nullable=True)

    # pendiente_revision | auto_resuelto | aprobado | rechazado
    estado: Mapped[str] = mapped_column(String, default="pendiente_revision", index=True)

    creado_en: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    actualizado_en: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
