"""Pasa los casos de prueba por el guardian real (sin LLM, sin red) y cuenta cuantos marca como sospechosos, por categoria."""

import os
import sys
from collections import defaultdict

os.environ.setdefault("GROQ_API_KEY", "dummy-para-medir")

from sqlalchemy import select  # noqa: E402

from app.db.models import CasoPrueba  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.graph.nodes import guardian  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cuenta = defaultdict(lambda: [0, 0])
    with SessionLocal() as db:
        for c in db.scalars(select(CasoPrueba)):
            r = guardian({"asunto": c.asunto, "cuerpo_mensaje": c.cuerpo_mensaje, "numero_pedido": None})
            cuenta[c.categoria][0] += 1
            cuenta[c.categoria][1] += bool(r["sospechoso"])
    print(f"{'categoria':<28}{'casos':>6}{'cazados':>9}{'%':>6}")
    for cat in sorted(cuenta, key=lambda k: (not k.startswith(("inj", "neg")), k)):
        n, caza = cuenta[cat]
        print(f"{cat:<28}{n:>6}{caza:>9}{100 * caza / n:>5.0f}%")


if __name__ == "__main__":
    main()
