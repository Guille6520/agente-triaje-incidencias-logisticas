# Agente de triaje de incidencias logísticas

Un sistema que recibe mensajes de clientes con incidencias de envío, los clasifica, los contrasta con los datos reales del pedido y prepara una respuesta. Lo inofensivo se responde solo. Lo que tiene consecuencias va a una persona, y de verdad se queda esperando a que esa persona decida.

Está construido como un grafo de LangGraph con seis capas, sobre la idea de que **la seguridad está en la arquitectura, no en confiar en que el modelo acierte siempre**.

Gestioné incidencias de transporte a mano durante seis años como jefe de tráfico. Este proyecto automatiza ese trabajo, y el diseño sale de ahí más que de ningún curso.

---

## De notebook a producción

Este proyecto empezó como un notebook de Colab para probar una idea de arquitectura de seguridad, con ataques reales incluidos (prompt injection, fraude por valor inflado, autoridades inventadas...). Ese notebook sigue intacto en [`prototipo/`](prototipo/), con su propio README explicando qué se probó y qué se rompió.

Esta segunda fase toma esa misma lógica de negocio (sin cambiarla) y la lleva a algo que se puede desplegar y usar de verdad:

| | Prototipo (`prototipo/`) | Producción (`app/`) |
|---|---|---|
| Entrada/salida | Celdas de notebook, a mano | API REST + demo web |
| Base de datos | SQLite en el propio Colab | PostgreSQL |
| Control humano | Solo enrutado (etiqueta, no bloqueo) | Bloqueo real con `interrupt()` de LangGraph: el grafo se pausa de verdad |
| Pruebas | 18 celdas manuales | pytest + CI en GitHub Actions |
| Configuración | API key en secretos de Colab | Variables de entorno (`.env`) |
| Despliegue | Ninguno | Docker Compose |

---

## El recorrido de un mensaje

```
guardian → clasificar → enriquecer → decidir → verificar → revisar_humano / auto_resuelto
 (reglas)    (LLM)      (base datos)  (reglas    (LLM juez)     ↑
                                       + LLM)                    │
                                                    aquí el grafo se PAUSA de verdad
                                                    hasta que alguien aprueba o rechaza
```

Las vías están dibujadas de antemano. El modelo trabaja dentro de los nodos, pero no elige el camino. La única salida que evita a un humano es `auto_resuelto`, y solo la alcanzan los casos 100% deterministas (plantillas fijas de Python, sin texto libre de un LLM de por medio).

### Las seis capas

1. **Guardián — sin LLM.** Reglas baratas que cazan lo evidente antes de gastar una llamada al modelo.
2. **Clasificar — con LLM.** Extrae tipo, urgencia, transportista y número de pedido con salida estructurada (`Literal` de Pydantic).
3. **Enriquecer — sin LLM.** Contrasta el mensaje con la base de datos real: si el pedido existe, si quien escribe es el titular, si lo que cuenta cuadra.
4. **Decidir — reglas + LLM.** Tres niveles: casos mecánicos que se auto-resuelven con plantillas fijas, reglas que escalan lo crítico, y el LLM solo para los casos grises de bajo riesgo.
5. **Verificar — con LLM.** El juez de salida: revisa que el borrador no prometa dinero, no filtre datos de otros pedidos, ni se salga del papel.
6. **Revisar humano.** Todo lo que no es 100% determinista se pausa aquí (`interrupt()`, persistido en Postgres) hasta que una persona lo aprueba o lo rechaza desde el panel.

### Segunda opinión opcional: Clef

Hay un nodo extra, `opinion_clef`, que antes del guardián le pregunta a [Clef](https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/) (un modelo de Cloudflare que devuelve probabilidades en vez de texto) dos cosas: si el mensaje intenta dar órdenes al sistema y si afirma una aprobación que no existe. Está apagado por defecto y, encendido, funciona **en modo sombra**: guarda las dos probabilidades en la incidencia y las expone en la API (`clef_manipulacion`, `clef_autorizacion`, `clef_alerta`), pero **no cambia el enrutado**, y si Clef falla el mensaje sigue su camino como si no existiera. Para encenderlo hacen falta `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` y `CLEF_MODO=sombra` en el `.env`.

---

## Cómo ejecutarlo

```bash
cp .env.example .env
# edita .env y pon tu GROQ_API_KEY (gratis en console.groq.com)
docker compose up --build
```

- Formulario para simular un mensaje entrante: http://localhost:8000/
- Panel de revisión humana: http://localhost:8000/revision (usuario/contraseña de `.env`)
- Documentación interactiva de la API: http://localhost:8000/docs

### Cómo se ve

El formulario para simular un mensaje entrante:

![Formulario para simular un mensaje de cliente](docs/capturas/formulario.webp)

Y el resultado de un caso que el sistema resuelve solo: un daño sin foto, al que contesta pidiéndola con una plantilla fija.

![Resultado de un caso auto-resuelto](docs/capturas/resultado.webp)

## Cómo correr los tests

```bash
pip install -r requirements-dev.txt
pytest
```

Los tests de las capas deterministas (guardián, enriquecer, decidir) y el mecanismo de `interrupt()` no necesitan ninguna clave. Los 18 casos de seguridad del notebook original (`tests/test_seguridad.py`) sí necesitan una `GROQ_API_KEY` real — se saltan solos si no la tienen, tanto en local como en CI.

---

## Cómo se ha medido

En `scripts/` está todo lo necesario para repetir las medidas:

- `generar_datos.py` y `generar_casos_v2.py`: 5.000 pedidos sintéticos y 5.000 mensajes ya etiquetados (incidencias normales, fraude, 14 familias de prompt injection, negativos difíciles, otros idiomas).
- `evaluar_casos.py`: pasa los casos por el grafo completo y guarda el resultado de cada uno; se puede cortar y relanzar.
- `medir_guardian.py`: cuántas inyecciones caza el guardián, sin gastar nada de LLM. De las 1.400 inyecciones nuevas caza 83 (el 6 %).
- `clef_replay.py`: pasa los casos por Clef. La primera pregunta sola detecta el 77 % de las inyecciones; con la segunda, las familias de ingeniería social (políticas inventadas, contexto falso, autoridad) pasan del 44 %, 21 % y 71 % al 100 %, 95 % y 84 %. Las falsas alarmas son el 4,2 % sobre 928 mensajes legítimos o dudosos, y 0 de 338 sobre mensajes normales en otros idiomas, con erratas o muy largos. También probé Clef-flash (9B, unas seis veces más barato): con la primera pregunta detecta la mitad que el modelo grande (36 % frente a 69 % con las mismas falsas alarmas), así que el proyecto usa el grande.

Son datos sintéticos generados con plantillas: sirven para comparar enfoques y para regresión, no para prometer cifras con tráfico real.

---

## Stack

- **LangGraph** para el grafo de estados, con **PostgreSQL** como backend del checkpointer (lo que hace posible el `interrupt()` real)
- **gpt-oss-120b vía Groq** como modelo — gratis, y coherente con la idea del proyecto: no le confío la seguridad al modelo, de eso se encargan las capas deterministas
- **FastAPI** para la API y el panel web (Jinja2)
- **SQLAlchemy + Alembic** para los datos de negocio (pedidos, incidencias) sobre PostgreSQL
- **pytest + GitHub Actions** para las pruebas, incluyendo regresión de seguridad
- **Clef (Cloudflare Workers AI)**, opcional, como segunda opinión con probabilidades en modo sombra

---

## Limitaciones, dichas claras

- Los datos son de prueba: la app arranca con cuatro pedidos, uno preparado a propósito para el caso de fraude por valor inflado (igual que en el prototipo), y `scripts/generar_datos.py` carga 5.000 más. Ninguna cifra de esta página sale de tráfico real.
- No hay envío real de email/tickets: la "respuesta enviada" es el texto final que el sistema produce, no una integración con un proveedor de correo o un ticketing real. Añadirla es cuestión de un adaptador en `app/api/` o `app/web/`, no de tocar el grafo.
- El panel de revisión usa autenticación básica de un solo usuario; para varios revisores haría falta gestión de usuarios de verdad.

---

## Licencia

MIT
