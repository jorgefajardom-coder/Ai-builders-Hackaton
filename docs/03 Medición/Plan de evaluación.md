---
tags: [medicion]
---
# Plan de evaluación

> [!important] El set oculto llama `/__reset` y luego manda requests que compara contra el original. Nuestro tester diferencial hace lo mismo con el corpus grabado ([[ADR-003]]).

## Unidad de prueba
Un **caso** = `reset` + secuencia de N requests. Cada respuesta se compara contra la grabada del original.

## Métricas
> [!note] Comparador idéntico al del jurado (README)
> Mismo status **y** mismo cuerpo. Si ambos cuerpos son JSON: el orden de las claves no importa, pero arrays, strings y números deben ser idénticos. Si alguno no es JSON: texto exacto. **Los headers no se comparan.** 5 s por paso.

| Métrica | Definición exacta | Umbral objetivo |
|---|---|---|
| **Tests pasados (oficial)** | Los 100 tests del jurado, consultados en `/evento/resultados` | ≥ 90/100 |
| **Paridad de casos (local)** | % de secuencias de nuestro corpus en las que **todas** las respuestas coinciden según el comparador del jurado | ≥ 90% en hold-out |
| **Paridad de pasos** | % de respuestas individuales iguales | ≥ 97% |
| **Paridad de status** | % de respuestas con el mismo código HTTP | ≥ 99% |
| **Mezcla del jurado** | Paridad de casos ponderada como el set: 40% de 1 request, 45% de 2–5 y 15% de 6–12 | ≥ 90% |
| **Brecha dev → hold-out** | Paridad en dev − paridad en hold-out | < 5 pts (si es mayor, estamos sobreajustando) |
| **Cobertura** | Rutas, métodos y códigos de error distintos observados en el original y respaldados en la spec | Crece en cada iteración; reportar el número |
| **Disponibilidad** | `/health` 200 y latencia p95 contra el despliegue | 200 siempre; p95 < 1 s (límite: 5 s) |
| **Spec respaldada** | % de filas de la spec con al menos un `id` del log; afirmaciones `confirmado` sin repetición | 100% con evidencia; 0 afirmaciones sin probar marcadas `confirmado` |
| **Presupuesto** | Requests usados del cupo de 8.000/día por token | < 6.000 antes de las 18:00 (reserva para revalidar el incidente) |

Todas se reportan **desglosadas por categoría**: éxito · error de validación · auth · ruta inexistente · método no permitido · secuencia con estado.

## Casos de prueba
| ID | Tipo | Qué prueba | Viene de |
|---|---|---|---|
| T-health | contrato | `GET /health` con token → 200 | [[Brief]] |
| T-reset | contrato | `POST /__reset` con token restaura el estado; con token ajeno o sin token responde como el original | [[Brief]], S5 |
| T-404 | ruta inexistente | Rutas aleatorias, profundas, con caracteres raros | H1 |
| T-405 | método | Cada método (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS) en cada ruta conocida | H1 |
| T-slash | formato de ruta | `/x` vs `/x/` vs `/X` vs `//x` vs query strings | H1 |
| T-auth-* | auth | Sin header, `Bearer` vacío, token incorrecto, esquema en minúsculas, espacios extra | H4 |
| T-body-* | validación | JSON inválido, vacío, tipos y campos incorrectos, `Content-Type` incorrecto | H5 |
| T-edge-* | límites | Strings largos, números extremos, unicode, valores negativos y vacíos | H8 |
| T-seq-* | estado | Crear → leer → modificar → borrar → leer; operaciones repetidas; orden alterado | H2 |
| T-det | determinismo | Misma secuencia 2 veces tras reset → ¿respuestas idénticas? | H3 |
| T-format | formato | Comparación byte a byte (espacios, orden de claves, salto de línea final) | H6 |

## Cómo se corre
```bash
python -m bench.diff --target http://localhost:8000 --split holdout
```

## Resultados
| Hora | Versión | Estricta | Status | Normalizada | Casos | Notas |
|---|---|---|---|---|---|---|
