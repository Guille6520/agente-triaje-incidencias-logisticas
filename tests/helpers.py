from langgraph.types import Command

from app.graph.schemas import IncidenciaState


def estado_inicial(mensaje: dict) -> dict:
    estado = {k: None for k in IncidenciaState.__annotations__}
    estado.update({
        "email_id": mensaje.get("id", "T1"),
        "remitente": mensaje["remitente"],
        "asunto": mensaje.get("asunto"),
        "cuerpo_mensaje": mensaje["cuerpo"],
        "aprobada_por_humano": False,
    })
    return estado


def ejecutar(grafo, mensaje: dict, thread_id: str, aprobar_si_escala: bool = True) -> dict:
    """Corre el mensaje por el grafo. Si se pausa (interrupt), reanuda con la
    decision humana indicada, para poder comprobar el resultado final."""
    config = {"configurable": {"thread_id": thread_id}}
    resultado = grafo.invoke(estado_inicial(mensaje), config=config)
    if "__interrupt__" in resultado:
        resultado = grafo.invoke(Command(resume={"aprobado": aprobar_si_escala}), config=config)
    return resultado


def se_escalo(resultado: dict) -> bool:
    return resultado.get("nodo_actual") == "revisar_humano"


def se_auto_resolvio(resultado: dict) -> bool:
    return resultado.get("nodo_actual") == "auto_resuelto"
