"""Pasa los casos de prueba por el grafo y guarda cada resultado; se puede cortar y relanzar sin repetir casos."""

import argparse
import re
import time
from collections import defaultdict

import groq
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import select

from app.config import settings
from app.db.models import CasoPrueba, ResultadoPrueba
from app.db.session import SessionLocal
from app.graph import nodes
from app.graph.graph import crear_grafo
from app.graph.service import _estado_inicial


class CuotaAgotada(Exception):
    pass


class _LLMConRegistro:
    """Envuelve el LLM de nodes.py para saber si una llamada falló por límite de ritmo,
    porque los nodos se tragan las excepciones y lo convertirían en un falso 'humano'."""

    def __init__(self, real):
        self._real = real
        self.errores = []
        self.llamadas = 0

    def with_structured_output(self, schema):
        real = self._real.with_structured_output(schema)
        registro = self

        class _Envoltorio:
            def invoke(self, mensajes):
                registro.llamadas += 1
                try:
                    return real.invoke(mensajes)
                except Exception as e:
                    registro.errores.append(e)
                    raise

        return _Envoltorio()


def _es_rate_limit(e):
    texto = str(e).lower()
    return isinstance(e, groq.RateLimitError) or "rate limit" in texto or "429" in texto


def _es_limite_diario(texto):
    t = texto.lower()
    return "per day" in t or "tpd" in t or "rpd" in t


def _espera(texto):
    m = re.search(r"try again in (?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", texto)
    segundos = 30.0
    if m and (m.group(1) or m.group(2)):
        segundos = int(m.group(1) or 0) * 60 + float(m.group(2) or 0)
    return min(max(segundos, 5.0), 90.0)


class FalloPersistente(Exception):
    pass


def _ejecutar(grafo, registro, caso, intentos=5):
    """Reintenta ante CUALQUIER fallo del LLM, no solo limite de ritmo: un 503, un timeout o
    cualquier otro tropiezo puntual de la API se tragaba en nodes.py y se guardaba como si
    fuera un veredicto real del modelo (asi se colaron miles de falsos 'fuera_de_alcance'
    el 26 de septiembre). Si tras varios intentos el fallo persiste, no se guarda nada: el
    caso se queda pendiente para la proxima vez, en vez de contaminar la tabla de resultados."""
    mensaje = {"email_id": f"caso-{caso.id}", "remitente": caso.remitente,
               "asunto": caso.asunto, "cuerpo_mensaje": caso.cuerpo_mensaje}
    ultimo = None
    for intento in range(intentos):
        registro.errores.clear()
        registro.llamadas = 0
        config = {"configurable": {"thread_id": f"caso-{caso.id}-{intento}"}}
        resultado = grafo.invoke(_estado_inicial(mensaje), config=config)
        if not registro.errores:
            return resultado, registro.llamadas
        ultimo = registro.errores[-1]
        texto = str(ultimo)
        if _es_limite_diario(texto):
            raise CuotaAgotada(texto)
        if _es_rate_limit(ultimo):
            espera = _espera(texto)
            print(f"   límite por minuto, espero {espera:.0f}s")
        else:
            espera = min(5 * 2 ** intento, 60)
            print(f"   {type(ultimo).__name__}: {texto[:100]}, espero {espera:.0f}s")
        time.sleep(espera)
    raise FalloPersistente(f"caso {caso.id}: sigue fallando tras {intentos} intentos: {ultimo}")


def _camino(resultado):
    if resultado.get("nodo_actual") == "auto_resuelto":
        return "auto_resuelto"
    if resultado.get("sospechoso") and not resultado.get("tipo_incidencia"):
        return "sospechoso"
    return "humano"


def _fila(caso, motor, resultado, llamadas):
    camino = _camino(resultado)
    tipo, urgencia = resultado.get("tipo_incidencia"), resultado.get("urgencia")
    return ResultadoPrueba(
        caso_id=caso.id, motor=motor, camino_obtenido=camino, tipo_obtenido=tipo, urgencia_obtenida=urgencia,
        motivo=resultado.get("motivo_decision") or resultado.get("motivo_sospecha"), llamadas_llm=llamadas,
        acierto_camino=camino == caso.camino_esperado,
        acierto_tipo=None if tipo is None else tipo == caso.tipo_esperado,
        acierto_urgencia=None if urgencia is None else urgencia == caso.urgencia_esperada,
        fallo_critico=camino == "auto_resuelto" and caso.camino_esperado != "auto_resuelto",
    )


def _intercalar(casos):
    """Ordena para que cualquier tramo del principio sea una muestra proporcional de todas las categorías."""
    por_categoria = defaultdict(list)
    for c in casos:
        por_categoria[c.categoria].append(c)
    clave = []
    for lista in por_categoria.values():
        for i, c in enumerate(lista):
            clave.append(((i + 0.5) / len(lista), c.categoria, c.id, c))
    return [c for *_, c in sorted(clave, key=lambda t: t[:3])]


def _pct(parte, total):
    return "  -  " if total == 0 else f"{100 * parte / total:4.0f}%"


def informe(motor):
    stats = defaultdict(lambda: defaultdict(int))
    with SessionLocal() as db:
        filas = db.execute(
            select(CasoPrueba.categoria, ResultadoPrueba).join(ResultadoPrueba, ResultadoPrueba.caso_id == CasoPrueba.id)
            .where(ResultadoPrueba.motor == motor)
        ).all()
    for categoria, r in filas:
        for clave in (categoria, "TOTAL"):
            s = stats[clave]
            s["n"] += 1
            s["camino"] += r.acierto_camino
            s["critico"] += r.fallo_critico
            s["llamadas"] += r.llamadas_llm
            if r.acierto_tipo is not None:
                s["n_tipo"] += 1
                s["tipo"] += r.acierto_tipo
            if r.acierto_urgencia is not None:
                s["n_urg"] += 1
                s["urgencia"] += r.acierto_urgencia
    print(f"\nMotor: {motor}")
    print(f"{'categoría':<24}{'casos':>6}{'camino':>8}{'tipo':>7}{'urgencia':>10}{'críticos':>10}{'llamadas':>10}")
    for clave in sorted(stats, key=lambda k: (k == "TOTAL", k)):
        s = stats[clave]
        print(f"{clave:<24}{s['n']:>6}{_pct(s['camino'], s['n']):>8}{_pct(s['tipo'], s['n_tipo']):>7}"
              f"{_pct(s['urgencia'], s['n_urg']):>10}{s['critico']:>10}{s['llamadas']:>10}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", help="etiqueta del motor; por defecto groq:<modelo>")
    parser.add_argument("--limite", type=int, default=0, help="máximo de casos en esta ejecución (0 = todos)")
    parser.add_argument("--categoria", help="solo esta categoría")
    parser.add_argument("--informe", action="store_true", help="solo mostrar el informe, sin ejecutar nada")
    args = parser.parse_args()
    motor = args.motor or f"groq:{settings.modelo_llm}"

    if args.informe:
        informe(motor)
        return

    registro = _LLMConRegistro(nodes.llm)
    nodes.llm = registro
    grafo = crear_grafo(MemorySaver())

    with SessionLocal() as db:
        hechos = set(db.scalars(select(ResultadoPrueba.caso_id).where(ResultadoPrueba.motor == motor)))
        casos = [c for c in db.scalars(select(CasoPrueba))
                 if c.id not in hechos and (not args.categoria or c.categoria == args.categoria)]
        casos = _intercalar(casos)
        if args.limite:
            casos = casos[:args.limite]
        print(f"{len(hechos)} ya hechos, {len(casos)} por hacer con {motor}")
        saltados = 0
        try:
            for i, caso in enumerate(casos, 1):
                try:
                    resultado, llamadas = _ejecutar(grafo, registro, caso)
                except FalloPersistente as e:
                    saltados += 1
                    print(f"[{i}/{len(casos)}] {caso.categoria:<22} SALTADO: {e}")
                    continue
                fila = _fila(caso, motor, resultado, llamadas)
                db.add(fila)
                db.commit()
                marca = "OK" if fila.acierto_camino else "FALLO"
                print(f"[{i}/{len(casos)}] {caso.categoria:<22} esperado={caso.camino_esperado:<13} "
                      f"obtenido={fila.camino_obtenido:<13} {marca}{' CRITICO' if fila.fallo_critico else ''}")
        except CuotaAgotada:
            print("\nCuota agotada. Relánzalo cuando se renueve y sigue por donde lo dejó.")
        except KeyboardInterrupt:
            print("\nParado a mano. Lo ya hecho está guardado.")
        if saltados:
            print(f"\n{saltados} casos saltados por fallos persistentes del LLM; siguen pendientes para el próximo relanzamiento.")
    informe(motor)


if __name__ == "__main__":
    main()
