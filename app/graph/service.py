"""Hace de puente entre el grafo (que lleva su propio checkpointer de LangGraph)
y la tabla `incidencias` de SQLAlchemy. Asi la API y el panel pueden listar y
mostrar casos sin tener que entender el protocolo de checkpoints de LangGraph."""

import uuid

from langgraph.types import Command
from sqlalchemy.orm import Session

from app.db.models import Incidencia
from app.graph.schemas import IncidenciaState

CAMPOS_ESTADO_INICIAL = list(IncidenciaState.__annotations__)


def _estado_inicial(mensaje: dict) -> dict:
    estado = {k: None for k in CAMPOS_ESTADO_INICIAL}
    estado.update({
        "email_id": mensaje["email_id"],
        "remitente": mensaje["remitente"],
        "asunto": mensaje.get("asunto"),
        "cuerpo_mensaje": mensaje["cuerpo_mensaje"],
        "aprobada_por_humano": False,
    })
    return estado


def procesar_mensaje(grafo, mensaje: dict, db: Session) -> Incidencia:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    resultado = grafo.invoke(_estado_inicial(mensaje), config=config)

    pausado = "__interrupt__" in resultado
    estado = "auto_resuelto" if resultado.get("nodo_actual") == "auto_resuelto" else "pendiente_revision"
    if not pausado and estado == "pendiente_revision":
        # No deberia pasar nunca -- todo camino que no acaba en auto_resuelto pasa
        # por revisar_humano, que siempre interrumpe -- pero si pasa, que no se
        # cuele en silencio.
        estado = "pendiente_revision"

    incidencia = Incidencia(
        thread_id=thread_id,
        email_id=mensaje["email_id"],
        remitente=mensaje["remitente"],
        asunto=mensaje.get("asunto"),
        cuerpo_mensaje=mensaje["cuerpo_mensaje"],
        tipo_incidencia=resultado.get("tipo_incidencia"),
        urgencia=resultado.get("urgencia"),
        resumen=resultado.get("resumen"),
        numero_pedido=resultado.get("numero_pedido"),
        sospechoso=resultado.get("sospechoso"),
        discrepancia=resultado.get("discrepancia"),
        motivo_decision=resultado.get("motivo_decision"),
        motivo_verificacion=resultado.get("motivo_verificacion"),
        respuesta_borrador=resultado.get("respuesta_borrador"),
        respuesta_final=resultado.get("respuesta_final"),
        estado=estado,
    )
    db.add(incidencia)
    db.commit()
    db.refresh(incidencia)
    return incidencia


class CasoNoPendienteError(Exception):
    pass


def revisar_caso(grafo, thread_id: str, aprobado: bool, db: Session) -> Incidencia:
    incidencia = db.query(Incidencia).filter_by(thread_id=thread_id).one_or_none()
    if incidencia is None:
        raise LookupError(f"No existe la incidencia {thread_id}")
    if incidencia.estado != "pendiente_revision":
        raise CasoNoPendienteError(f"La incidencia {thread_id} ya esta en estado '{incidencia.estado}'")

    config = {"configurable": {"thread_id": thread_id}}
    resultado = grafo.invoke(Command(resume={"aprobado": aprobado}), config=config)

    incidencia.estado = "aprobado" if aprobado else "rechazado"
    incidencia.respuesta_final = resultado.get("respuesta_final")
    db.commit()
    db.refresh(incidencia)
    return incidencia


def listar_pendientes(db: Session) -> list[Incidencia]:
    return (
        db.query(Incidencia)
        .filter_by(estado="pendiente_revision")
        .order_by(Incidencia.creado_en)
        .all()
    )
