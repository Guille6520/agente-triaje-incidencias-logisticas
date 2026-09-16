from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.schemas import IncidenciaOut, MensajeEntrante, RevisionRequest
from app.api.security import requiere_revisor
from app.db.models import Incidencia
from app.db.session import get_db
from app.graph.service import CasoNoPendienteError, procesar_mensaje, revisar_caso

router = APIRouter(prefix="/api", tags=["incidencias"])


@router.post("/incidencias", response_model=IncidenciaOut)
def crear_incidencia(mensaje: MensajeEntrante, request: Request, db: Session = Depends(get_db)):
    """Simula que llega una incidencia nueva -- en un sistema real esto seria
    el webhook de un ticketing, un correo entrante, lo que sea."""
    return procesar_mensaje(request.app.state.grafo, mensaje.model_dump(), db)


@router.get("/incidencias", response_model=list[IncidenciaOut])
def listar_incidencias(
    estado: str | None = None,
    db: Session = Depends(get_db),
    _revisor: str = Depends(requiere_revisor),
):
    consulta = db.query(Incidencia)
    if estado:
        consulta = consulta.filter_by(estado=estado)
    return consulta.order_by(Incidencia.creado_en.desc()).all()


@router.get("/incidencias/{thread_id}", response_model=IncidenciaOut)
def obtener_incidencia(
    thread_id: str,
    db: Session = Depends(get_db),
    _revisor: str = Depends(requiere_revisor),
):
    incidencia = db.query(Incidencia).filter_by(thread_id=thread_id).one_or_none()
    if incidencia is None:
        raise HTTPException(status_code=404, detail="No encontrada")
    return incidencia


@router.post("/incidencias/{thread_id}/revision", response_model=IncidenciaOut)
def revisar(
    thread_id: str,
    cuerpo: RevisionRequest,
    request: Request,
    db: Session = Depends(get_db),
    _revisor: str = Depends(requiere_revisor),
):
    try:
        return revisar_caso(request.app.state.grafo, thread_id, cuerpo.aprobado, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CasoNoPendienteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
