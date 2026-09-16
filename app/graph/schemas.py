from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal, TypedDict


class ClasificacionIncidencia(BaseModel):
    """Lo que devuelve clasificar. Los Literal cierran los valores posibles."""

    tipo: Literal[
        "retraso", "daño", "perdida", "entrega_incorrecta",
        "faltan_bultos", "consulta_seguimiento", "fuera_de_alcance",
    ] = Field(description="Tipo de incidencia")
    urgencia: Literal["alta", "media", "baja"] = Field(description="Nivel de urgencia")
    resumen: str = Field(description="La incidencia en dos frases")
    transportista: str = Field(description="La mensajería, o 'desconocido'")
    numero_pedido: str = Field(description="El número de pedido, o 'desconocido'")


class DecisionAgente(BaseModel):
    puede_resolver: bool = Field(description="True si el agente lo gestiona, False si va a humano")
    motivo: str = Field(description="Por que")
    respuesta_borrador: str = Field(description="Borrador de respuesta")


class VeredictoVerificador(BaseModel):
    """El juez de salida (patron LLM-as-judge)."""

    es_segura: bool = Field(description="False si promete dinero, filtra datos o cambia de rol")
    motivo: str = Field(description="Por que es segura o no")


class IncidenciaState(TypedDict):
    # Lo que entra
    email_id: str
    remitente: str
    asunto: Optional[str]
    cuerpo_mensaje: str
    # Guardian
    sospechoso: Optional[bool]
    motivo_sospecha: Optional[str]
    # Clasificar
    tipo_incidencia: Optional[str]
    urgencia: Optional[str]
    resumen: Optional[str]
    transportista: Optional[str]
    numero_pedido: Optional[str]
    # Enriquecer
    pedido_existe: Optional[bool]
    valor_real_pedido: Optional[float]
    estado_real_pedido: Optional[str]
    titular_coincide: Optional[bool]
    tiene_foto: Optional[bool]
    discrepancia: Optional[str]
    # Decidir
    puede_resolver: Optional[bool]
    motivo_decision: Optional[str]
    auto_resuelto: Optional[bool]
    # Resolver y verificar
    respuesta_borrador: Optional[str]
    respuesta_segura: Optional[bool]
    motivo_verificacion: Optional[str]
    # Final
    respuesta_final: Optional[str]
    aprobada_por_humano: Optional[bool]
    error: Optional[str]
    nodo_actual: Optional[str]
