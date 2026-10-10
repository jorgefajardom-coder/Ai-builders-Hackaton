---
tags: [problema]
---
# Supuestos y alcance

> [!note] Los supuestos marcados con ❓ se confirman o descartan con un experimento y se registran en el [[Log de experimentos]].

## Supuestos
| # | Supuesto | Por qué lo asumimos | Qué pasa si es falso |
|---|---|---|---|
| S1 ✅ | El servicio es HTTP, con mensajes en `POST /msg` | **Confirmado por el README** | — |
| S2 ✅ | Tiene **estado** (cuentas, saldos, operaciones) | README + ejemplos (IDs secuenciales, saldos) | — |
| S3 ✅ | El set evalúa **secuencias** desde `/__reset` (40 de 1 request, 45 de 2–5, 15 de 6–12) | README | — |
| S4 ❓ | Determinista tras un reset (IDs secuenciales `AC-0001`, `OP-0001`; sin timestamps) | Ejemplos | Si hay aleatoriedad, esos tests son imposibles de igualar; se documenta como riesgo |
| S5 ❓ | `/__reset` sin token o con un token ajeno devuelve un error de auth del original | El contrato pide "responder como el original" | Se mide en vivo y se copia tal cual |
| S6 ❓ | El reemplazo solo necesita **un** estado (el del token del equipo); cualquier otro token o la falta de token se responde como lo haría el original con un token inválido | El set usa el token del equipo; el original separa el estado por token | Si el set usara varios tokens válidos, habría que separar el estado por token (cambio pequeño: un dict de estados) |
| S7 ✅ | **Los headers no se comparan**; el body JSON se compara sin importar el orden de las claves | README | — |
| S8 ❓ | El control es una función determinista solo del contenido del mensaje (sin estado ni token) | Mismo mensaje → mismo control en #5 y #11 | Si dependiera del estado, la integridad sería parte de la memoria |
| S9 | La versión de las 20:00 puede diferir de la de la mañana | README: "el servicio puede cambiar durante el día" | Re-grabar la regresión antes de las 20:00 y comparar con el corpus de la mañana ([[ADR-003]]) |
| S10 | Lo que el reemplazo no sepa responder recibe un default explícito, documentado como `supuesto` en la spec | README lo pide | — |

## Dentro del alcance
- Todos los métodos, rutas (existentes e inexistentes), headers y cuerpos que el original acepte o rechace.
- Errores: status, body, `Content-Type` y formato exactos.
- Comportamiento con estado entre requests desde un `/__reset`.
- Spec y log de experimentos respaldados con evidencia.

## Fuera del alcance
| Qué dejamos fuera | Razón |
|---|---|
| Igualar latencia y tiempos de respuesta | No es comportamiento funcional; solo hay que responder en < 5 s por paso |
| Igualar headers (incluido `X-Req`) | El set **no compara headers** (README). `X-Req` se registra en el log, pero no se persigue en el reemplazo salvo que sea trivial |
| Usar un LLM dentro del reemplazo | Está permitido, pero el servicio es determinista y basado en reglas: un LLM agrega latencia y no determinismo sin aportar paridad |
| Persistencia entre reinicios del servidor | El evaluador llama `/__reset` antes de cada test; el estado durable no aporta |
| Escalado horizontal / alta disponibilidad | Una sola instancia evita inconsistencias de estado; la carga del evaluador es baja |
| Reproducir bugs que dependen de concurrencia real | Difíciles de observar con certeza en 8 h; se documentan como hipótesis si aparecen |

Relacionado: [[Casos difíciles]] · [[Brief]]
