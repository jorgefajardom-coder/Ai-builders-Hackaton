---
tags: [arquitectura, moc]
---
# Registro de decisiones

> [!tip] Regla de la rúbrica
> Cada decisión dice qué alternativa descartó y por qué. Para una decisión nueva, crea una nota en `Decisiones/` con la plantilla [[Plantillas/Decisión]].

| ID | Decisión | Elegido | Descartado | Estado |
|---|---|---|---|---|
| [[ADR-001]] | Núcleo HTTP | Catch-all ASGI puro sobre uvicorn | Routing de FastAPI/Flask | propuesta |
| [[ADR-002]] | Dónde vive el estado | Memoria, 1 proceso, snapshot inicial | Base de datos (Redis/Postgres/SQLite) | propuesta |
| [[ADR-003]] | Cómo descubrimos y verificamos el comportamiento | Prober con log + ajuste offline + validación predictiva + replay diferencial | curl/Postman manual; herramientas automáticas | aplicada |
| [[ADR-004]] | Hosting | Railway, siempre encendido, 1 réplica; `/health` 200 sin token solo con `Host: healthcheck.railway.app` | Serverless; planes que se duermen; ruta `/healthz` extra | aceptada |
| ADR-005 | Lenguaje | Python 3.10 en el banco y en el reemplazo | Node / Go | propuesta |
| ADR-006 | Entradas desconocidas | Default explícito marcado `supuesto` | Adivinar en silencio / fallback a LLM | propuesta |
| ADR-007 | Confianza en la spec | `confirmado` solo con ≥ 2 repeticiones o una predicción sobre entrada no vista | Confirmar lo visto una sola vez | aplicada |

Detalle de las 7 decisiones con su justificación: README del repo → *Decisiones de Diseño*.
