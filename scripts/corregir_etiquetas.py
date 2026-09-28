"""Corrige en la base ya cargada la etiqueta de fraude_valor que no coincidia con el mensaje real
(el generador elegia la plantilla sin mirar el tipo asignado). Recalcula el acierto de tipo de
los resultados ya guardados que dependian de esa etiqueta. Idempotente: se puede correr mas de una vez."""

from sqlalchemy import select

from app.db.models import CasoPrueba, ResultadoPrueba
from app.db.session import SessionLocal


def _tipo_real(cuerpo: str) -> str | None:
    texto = cuerpo.lower()
    if "se ha roto" in texto:
        return "daño"
    if "no ha llegado" in texto:
        return "perdida"
    return None  # la tercera plantilla ("iba material...") no dice ni una cosa ni la otra


def main():
    with SessionLocal() as db:
        casos = db.scalars(select(CasoPrueba).where(CasoPrueba.categoria == "fraude_valor")).all()
        corregidos = {}
        for c in casos:
            real = _tipo_real(c.cuerpo_mensaje)
            if real and real != c.tipo_esperado:
                corregidos[c.id] = (c.tipo_esperado, real)
                c.tipo_esperado = real
        db.commit()
        print(f"{len(casos)} casos de fraude_valor revisados, {len(corregidos)} etiquetas corregidas")

        if corregidos:
            resultados = db.scalars(select(ResultadoPrueba).where(ResultadoPrueba.caso_id.in_(corregidos))).all()
            cambios = 0
            for r in resultados:
                _, tipo_correcto = corregidos[r.caso_id]
                nuevo = None if r.tipo_obtenido is None else r.tipo_obtenido == tipo_correcto
                if nuevo != r.acierto_tipo:
                    r.acierto_tipo = nuevo
                    cambios += 1
            db.commit()
            print(f"{len(resultados)} resultados ya guardados de esos casos, {cambios} con el acierto de tipo recalculado")


if __name__ == "__main__":
    main()
