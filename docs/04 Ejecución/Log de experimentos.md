---
tags: [ejecucion, reto2, entregable]
---
# Log de experimentos

> [!important] Entregable: `experimentos.jsonl` en la raíz del repo, **una línea por cada request que le mandamos al original**, sin excepciones. Lo genera el prober automáticamente; nunca se escribe a mano.

## Formato (README del material)
```json
{"id": 1, "seq": "s1", "x_req": 1, "hipotesis": "PING responde sin estado",
 "request": {"m": "PING;XX"}, "status": 200, "response": {"pong": true},
 "conclusion": "responde pong aunque el último campo no sea un número"}
```
| Campo | Qué es |
|---|---|
| `id` | Número de línea, único. **La spec cita estos números** |
| `seq` | Secuencia. Todas sus líneas van después de un reset |
| `x_req` | Valor del header `X-Req` de la respuesta |
| `hipotesis` | Qué estábamos probando |
| `request` / `status` / `response` | Lo enviado y lo recibido |
| `conclusion` | Qué aprendimos (opcional) |

## Reglas operativas
- El prober **nunca** guarda el header `Authorization` (credenciales por persona, repo público).
- Las respuestas con `X-Frontier-Infra: rate-limit` se marcan y **no** cuentan como comportamiento.
- Cada experimento se lanza con una `hipotesis` explícita. Las `conclusion` se completan después.
- Presupuesto: 8.000 req/día por token → usar un fuzzer dosificado, sin barridos ciegos.

## Resumen por bloque (para el debrief)
| Seq | Hora | Hipótesis | Requests | Conclusión |
|---|---|---|---|---|
| | | | | |

Baseline y métricas: [[Plan de evaluación]]
