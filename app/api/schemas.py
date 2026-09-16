from pydantic import BaseModel, ConfigDict


class MensajeEntrante(BaseModel):
    email_id: str
    remitente: str
    asunto: str | None = None
    cuerpo_mensaje: str


class RevisionRequest(BaseModel):
    aprobado: bool


class IncidenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    thread_id: str
    email_id: str
    remitente: str
    asunto: str | None
    cuerpo_mensaje: str
    tipo_incidencia: str | None
    urgencia: str | None
    resumen: str | None
    numero_pedido: str | None
    sospechoso: bool | None
    discrepancia: str | None
    motivo_decision: str | None
    motivo_verificacion: str | None
    respuesta_borrador: str | None
    respuesta_final: str | None
    estado: str
