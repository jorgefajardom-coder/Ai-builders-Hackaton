---
tags: [arquitectura, moc]
---
# Registro de decisiones

> [!tip] Regla de la rúbrica
> Cada decisión dice qué alternativa descartó y por qué. Para una decisión nueva, crea una nota en `Decisiones/` con la plantilla [[Plantillas/Decisión]].

| ID | Decisión | Elegido | Descartado | Estado |
|---|---|---|---|---|
| [[ADR-001]] | Núcleo HTTP | Catch-all ASGI puro sobre uvicorn `--workers 1 --no-server-header` + `try/except` global (nunca el 500 de uvicorn) | FastAPI, router de Starlette, aiohttp, `http.server` | aceptada |
| [[ADR-002]] | Dónde vive el estado | Memoria detrás del puerto `StateRepository`, separado por token; reset = función de estado inicial (IDs incluidos) | Redis/Postgres desplegado; `deepcopy`; contadores globales | aceptada |
| [[ADR-003]] | Cómo descubrimos y verificamos el comportamiento | Prober con log + ajuste offline + validación predictiva + replay diferencial | curl/Postman manual; herramientas automáticas | aplicada |
| [[ADR-004]] | Hosting | Railway, siempre encendido, 1 réplica; `/health` 200 sin token solo con `Host: healthcheck.railway.app` | Serverless; planes que se duermen; ruta `/healthz` extra | aceptada |
| ADR-005 | Lenguaje | Python 3.10 en el banco y en el reemplazo | Node / Go | aceptada |
| ADR-006 | Entradas desconocidas | Default explícito marcado `supuesto` | Adivinar en silencio / fallback a LLM | aceptada |
| ADR-007 | Confianza en la spec | `confirmado` solo con ≥ 2 repeticiones o una predicción sobre entrada no vista | Confirmar lo visto una sola vez | aplicada |
| ADR-008 | Estructura interna | Hexagonal mínima: adaptador HTTP → pipeline → registro → dominio puro → puertos | `app.py` monolítico con `if/elif`; Clean Architecture completa | aceptada |
| ADR-009 | Errores y precedencia | Catálogo de errores como datos (código, status, cuerpo exacto, etapa) + pipeline con orden declarado; los handlers lanzan `DomainError(code)` | `if` anidados con strings dispersos; validación con Pydantic | aceptada |
| ADR-010 | Comandos | Registro nombre → handler + aridad (un módulo por comando) | Dispatcher `if cmd == ...` | aceptada |
| ADR-011 | Cambio de las 15:30 | Perfiles heredables `BEHAVIOR_PROFILE=v1\|v2` (base + overrides) con goldens por perfil | Editar reglas en el sitio; flags `if INCIDENT`; ramas de git | aceptada |
| ADR-012 | Escalabilidad | App sin estado propio detrás del puerto; **1 réplica a propósito**; escalar = store compartido (Redis) particionado por token | Varias réplicas en memoria; Redis desde el día 1 | aceptada |
| ADR-013 | Anti-sobreajuste | Tester diferencial con hold-out (otra semilla); alarma si dev − hold-out ≥ 5 pts | Medir solo en dev o solo con el resultado oficial | aceptada |
| ADR-014 | Red de seguridad | Diferencial + goldens en pre-push, smoke post-deploy con token, logs JSON por request, secuencias centinela para la 15:30 | Tests manuales; OpenTelemetry/Prometheus | aceptada |

Investigación y fuentes: [[Investigación de arquitecturas]] · Entregables: `docs/entregables/`

Detalle de las decisiones con su justificación: README del repo → *Decisiones de Diseño*.
