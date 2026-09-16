import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.security import requiere_revisor
from app.db.session import get_db
from app.graph.service import CasoNoPendienteError, listar_pendientes, procesar_mensaje, revisar_caso

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.post("/")
def enviar_mensaje(
    request: Request,
    remitente: str = Form(...),
    asunto: str = Form(""),
    cuerpo_mensaje: str = Form(...),
    db: Session = Depends(get_db),
):
    mensaje = {
        "email_id": uuid.uuid4().hex[:8],
        "remitente": remitente,
        "asunto": asunto,
        "cuerpo_mensaje": cuerpo_mensaje,
    }
    incidencia = procesar_mensaje(request.app.state.grafo, mensaje, db)
    return templates.TemplateResponse(request, "resultado.html", {"incidencia": incidencia})


@router.get("/revision")
def bandeja(
    request: Request,
    db: Session = Depends(get_db),
    _revisor: str = Depends(requiere_revisor),
):
    pendientes = listar_pendientes(db)
    return templates.TemplateResponse(request, "revision.html", {"pendientes": pendientes})


@router.post("/revision/{thread_id}")
def resolver(
    thread_id: str,
    request: Request,
    aprobado: str = Form(...),
    db: Session = Depends(get_db),
    _revisor: str = Depends(requiere_revisor),
):
    try:
        revisar_caso(request.app.state.grafo, thread_id, aprobado == "si", db)
    except (LookupError, CasoNoPendienteError):
        pass
    return RedirectResponse(url="/revision", status_code=303)
