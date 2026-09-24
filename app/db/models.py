import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Pedido(Base):
    """La tabla contra la que se contrasta cada incidencia -- de esto vive la capa 'enriquecer'."""

    __tablename__ = "pedidos"

    numero_pedido: Mapped[str] = mapped_column(String, primary_key=True)
    titular_email: Mapped[str] = mapped_column(String)
    transportista: Mapped[str] = mapped_column(String)
    valor: Mapped[float] = mapped_column(Float)
    estado: Mapped[str] = mapped_column(String)
    tiene_foto: Mapped[bool] = mapped_column(Boolean)

    # Todo lo de abajo es nullable: los pedidos de prueba originales no lo traen.
    fecha_pedido: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    fecha_envio: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    fecha_entrega_prevista: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    fecha_entrega_real: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    provincia_destino: Mapped[str | None] = mapped_column(String, nullable=True)
    peso_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_bultos: Mapped[int | None] = mapped_column(nullable=True)
    categoria: Mapped[str | None] = mapped_column(String, nullable=True)
    perecedero: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Cliente(Base):
    """Se enlaza con pedidos por email a proposito, sin clave foranea: los pedidos de prueba originales no tienen cliente."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)  # particular | empresa
    empresa: Mapped[str | None] = mapped_column(String, nullable=True)
    fecha_alta: Mapped[datetime.date] = mapped_column(Date)
    reincidente: Mapped[bool] = mapped_column(Boolean, default=False)


class Transportista(Base):
    """Perfil de fiabilidad de cada transportista, para poder pesar sus incidencias."""

    __tablename__ = "transportistas"

    nombre: Mapped[str] = mapped_column(String, primary_key=True)
    zona: Mapped[str] = mapped_column(String)
    tasa_retraso: Mapped[float] = mapped_column(Float)
    tasa_dano: Mapped[float] = mapped_column(Float)
    tasa_perdida: Mapped[float] = mapped_column(Float)


class CasoPrueba(Base):
    """Un mensaje de cliente con la respuesta correcta ya etiquetada, para medir cualquier modelo contra el mismo banco."""

    __tablename__ = "casos_prueba"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_pedido: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    remitente: Mapped[str] = mapped_column(String)
    asunto: Mapped[str | None] = mapped_column(String, nullable=True)
    cuerpo_mensaje: Mapped[str] = mapped_column(Text)

    # limpio | fraude | injection | ... (lo define el generador)
    categoria: Mapped[str] = mapped_column(String, index=True)
    tipo_esperado: Mapped[str] = mapped_column(String)
    urgencia_esperada: Mapped[str] = mapped_column(String)
    # auto_resuelto | humano | sospechoso
    camino_esperado: Mapped[str] = mapped_column(String, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResultadoPrueba(Base):
    """Lo que hizo un motor (Groq, Jev...) con un caso de prueba. Un resultado por caso y motor."""

    __tablename__ = "resultados_prueba"
    __table_args__ = (UniqueConstraint("caso_id", "motor"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    caso_id: Mapped[int] = mapped_column(ForeignKey("casos_prueba.id"), index=True)
    motor: Mapped[str] = mapped_column(String, index=True)

    camino_obtenido: Mapped[str] = mapped_column(String)
    tipo_obtenido: Mapped[str | None] = mapped_column(String, nullable=True)
    urgencia_obtenida: Mapped[str | None] = mapped_column(String, nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    llamadas_llm: Mapped[int] = mapped_column(default=0)

    acierto_camino: Mapped[bool] = mapped_column(Boolean)
    acierto_tipo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    acierto_urgencia: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Se resolvió solo un caso que debía ir a una persona: el fallo grave.
    fallo_critico: Mapped[bool] = mapped_column(Boolean)

    creado_en: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class Incidencia(Base):
    """El registro de cada mensaje procesado. El thread_id es el enlace con el checkpoint de LangGraph."""

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
