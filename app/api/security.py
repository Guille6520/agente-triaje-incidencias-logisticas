import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

security = HTTPBasic()


def requiere_revisor(credenciales: HTTPBasicCredentials = Depends(security)) -> str:
    """Protege el panel de revision humana y los endpoints que aprueban casos.
    Basic auth simple: no hace falta gestion de usuarios para un panel de un solo rol."""
    usuario_ok = secrets.compare_digest(credenciales.username, settings.review_username)
    password_ok = secrets.compare_digest(credenciales.password, settings.review_password)
    if not (usuario_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credenciales.username
