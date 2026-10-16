from pydantic import BaseModel, ConfigDict, computed_field

from app.config import settings


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
    clef_manipulacion: float | None
    clef_autorizacion: float | None
    clef_estado: str | None
    motivo_decision: str | None
    motivo_verificacion: str | None
    respuesta_borrador: str | None
    respuesta_final: str | None
    estado: str

    @computed_field
    @property
    def clef_alerta(self) -> bool | None:
        ps = [p for p in (self.clef_manipulacion, self.clef_autorizacion) if p is not None]
        return max(ps) >= settings.clef_umbral if ps else None
