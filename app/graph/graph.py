"""El grafo de 6 capas del prototipo, con una diferencia clave de produccion:
en el notebook, 'escalar' y 'guardar' eran solo etiquetas de enrutado (no bloqueaban
nada). Aqui ambos casos convergen en `revisar_humano`, que llama a `interrupt()` y
PAUSA el grafo de verdad hasta que una persona aprueba o rechaza desde el panel.
Solo `auto_resuelto` (100% deterministico, sin texto libre de un LLM) sale sin pasar
por nadie -- que es justo el reparto de riesgo que describe el README del prototipo.
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
    # Segura o no, un borrador libre de un LLM siempre pasa por una persona.
    return "revisar_humano"


def crear_grafo(checkpointer):
    """El checkpointer es inyectable: MemorySaver en tests, PostgresSaver en produccion.
    Sin checkpointer, interrupt() no tiene donde guardar el estado y no puede pausar ni reanudar."""
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
