---
tags: [referencia, reto2]
---
# Reto 2 — La caja negra

> [!abstract] Enunciado
> Descubre cómo se comporta un servicio sin documentación y construye un reemplazo que responda exactamente igual, **errores incluidos**.
> Brief y contrato: [[Brief]] · README completo: `material/README.md` · Primeros hallazgos: [[Hallazgos iniciales]]

## Datos clave del material
| Tema | Dato |
|---|---|
| Original | `https://caja-negra-production-c64f.up.railway.app` |
| Tokens | Uno **por persona** (en `/evento`). **Cada token tiene su propio estado** → se puede explorar en paralelo |
| Protocolo | `POST /msg` con `{"m":"CMD;args;CONTROL"}` · `POST /__reset` · `GET /health` |
| Rate limit | 10 req/s y **8.000 req/día por token**. Si se excede: header `X-Frontier-Infra: rate-limit` (es de la infraestructura, no del servicio: **no** grabarla como comportamiento) |
| Header `X-Req` | Viene en cada respuesta y va al log (`x_req`) |
| Cambios | El servicio **puede cambiar durante el día**. Se evalúa contra la versión vigente a las **20:00** |
| 20:00 | Los tokens de participante **dejan de funcionar** contra el original → todo el corpus tiene que estar grabado antes |
| LLM | Se permite dentro del reemplazo si responde en < 5 s por paso |
| Instancias | El set le habla a un solo proceso → **una instancia** ([[ADR-002]]) |
| Llamar al original | Si el reemplazo lo hace, **el set vale 0** |

## Cómo se evalúa
- **100 tests**: 40 de 1 request, 45 secuencias de 2–5 y 15 de 6–12. Cada uno empieza con `POST /__reset`. Ninguno repite la secuencia de ejemplo.
- Pasa si **cada** respuesta tiene el **mismo status** y el **mismo cuerpo**: si es JSON, el orden de claves no importa, pero arrays, strings y números deben ser idénticos; si no es JSON, se compara el texto exacto.
- **Los headers no se comparan.** 5 s por paso.
- Se puede validar en `/evento` y ver el resultado en `/evento/resultados` → **feedback real durante el día**.
- **Spec:** un juez la compara con la lista completa de comportamientos. Cuenta cada uno bien descrito **y que cite una línea del log**. **Una afirmación falsa resta.**

## Entregables extra
- **Especificación** → [[Especificación]] (estructura fija de 7 secciones)
- **`experimentos.jsonl`** → [[Log de experimentos]] (una línea por request al original)

## Preguntas abiertas
Resueltas en `spec/ESPECIFICACION.md` (control, precedencia, ANULA, montos, nombres, X-Req, NOTAS, HALT, antifraude). Lo que sigue abierto está marcado como **supuesto** (SU-01…SU-05) y lo que cambie a las 15:30 lo detecta el [[Centinela]].
