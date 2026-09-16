"""El mismo grafo de 6 capas del prototipo, con una diferencia de produccion que
importa: en el notebook, 'escalar' y 'guardar' eran solo etiquetas de enrutado,
no bloqueaban nada de verdad. Aqui los dos casos convergen en `revisar_humano`,
que llama a `interrupt()` y pausa el grafo de verdad hasta que alguien aprueba o
rechaza desde el panel. Lo unico que sale sin pasar por una persona es
`auto_resuelto` -- 100% deterministico, sin una linea de texto libre de un LLM --
que es exactamente el reparto de riesgo que ya explicaba el README del prototipo.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.graph.nodes import clasificar, decidir, enriquecer, guardian, verificar
from app.graph.schemas import IncidenciaState


def revisar_humano(state):
    decision = interrupt({
        "tipo_incidencia": state.get("tipo_incidencia"),
        "urgencia": state.get("urgencia"),
        "numero_pedido": state.get("numero_pedido"),
        "motivo_decision": state.get("motivo_decision"),
        "motivo_verificacion": state.get("motivo_verificacion"),
        "discrepancia": state.get("discrepancia"),
        "respuesta_borrador": state.get("respuesta_borrador"),
    })
    aprobado = bool(decision.get("aprobado"))
    return {
        "nodo_actual": "revisar_humano",
        "aprobada_por_humano": aprobado,
        "respuesta_final": state.get("respuesta_borrador") if aprobado else None,
    }


def auto_resuelto(state):
    return {"nodo_actual": "auto_resuelto", "respuesta_final": state.get("respuesta_borrador")}


def router_guardian(state):
    return "revisar_humano" if state.get("sospechoso") is True else "clasificar"


def router_decidir(state):
    if state.get("auto_resuelto") is True:
        return "auto_resuelto"
    if state.get("puede_resolver") is True:
        return "verificar"
    return "revisar_humano"


def router_verificar(_state):
    # Segura o no, un borrador escrito por el LLM pasa siempre por una persona.
    return "revisar_humano"


def crear_grafo(checkpointer):
    """El checkpointer se inyecta: MemorySaver en los tests, PostgresSaver en produccion.
    Sin el, interrupt() no tiene donde dejar el estado y no hay pausa ni reanudacion que valga."""
    b = StateGraph(IncidenciaState)
    b.add_node("guardian", guardian)
    b.add_node("clasificar", clasificar)
    b.add_node("enriquecer", enriquecer)
    b.add_node("decidir", decidir)
    b.add_node("verificar", verificar)
    b.add_node("revisar_humano", revisar_humano)
    b.add_node("auto_resuelto", auto_resuelto)

    b.add_edge(START, "guardian")
    b.add_conditional_edges("guardian", router_guardian, {"clasificar": "clasificar", "revisar_humano": "revisar_humano"})
    b.add_edge("clasificar", "enriquecer")
    b.add_edge("enriquecer", "decidir")
    b.add_conditional_edges("decidir", router_decidir, {"verificar": "verificar", "revisar_humano": "revisar_humano", "auto_resuelto": "auto_resuelto"})
    b.add_conditional_edges("verificar", router_verificar, {"revisar_humano": "revisar_humano"})
    b.add_edge("revisar_humano", END)
    b.add_edge("auto_resuelto", END)
    return b.compile(checkpointer=checkpointer)
