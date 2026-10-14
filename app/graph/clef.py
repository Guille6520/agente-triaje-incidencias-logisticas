"""Cliente minimo de Clef (Cloudflare Workers AI): preguntas tipadas y respuestas con probabilidades.
Usa el mismo formato que Jev (noul / choice / score), asi que cambiar de proveedor es cambiar esta capa."""

import random
import time

import httpx

from app.config import settings

MODELO = "clef"
REINTENTABLES = {429, 500, 502, 503, 504}
NEURONAS_POR_MILLON_TOKENS = {"clef": 21818, "clef-flash": 3455}


class ClefError(Exception):
    pass


class CuotaDiariaAgotada(ClefError):
    pass


def evaluar(state, questions, modelo=MODELO, reintentos=5):
    url = (f"https://api.cloudflare.com/client/v4/accounts/{settings.cloudflare_account_id}"
           f"/ai/run/@cf/cloudflare/{modelo}")
    cabeceras = {"Authorization": f"Bearer {settings.cloudflare_api_token}"}
    cuerpo = {"model": modelo, "state": state, "questions": questions}
    error = ""
    for intento in range(reintentos):
        inicio = time.perf_counter()
        try:
            r = httpx.post(url, headers=cabeceras, json=cuerpo, timeout=60)
        except httpx.HTTPError as e:
            error = f"{type(e).__name__}: {e}"
        else:
            if r.status_code == 200:
                resultado = r.json()["result"]
                return {
                    "answers": resultado["answers"],
                    "tokens_in": resultado["usage"]["input_tokens"],
                    "latencia_ms": (time.perf_counter() - inicio) * 1000,
                }
            error = f"{r.status_code}: {r.text[:200]}"
            if "daily" in r.text.lower() or "allocation" in r.text.lower():
                raise CuotaDiariaAgotada(error)
            if r.status_code not in REINTENTABLES:
                raise ClefError(error)
        time.sleep(min(2 ** intento, 30) + random.random())
    raise ClefError(error)
