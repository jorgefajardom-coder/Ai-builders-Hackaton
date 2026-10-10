---
tags: [medicion]
---
# Plan de evaluación

> [!important] En Ejecución hay un set de evaluaciones oculto. Nuestro set propio debe imitarlo.

## Métricas
| Métrica | Definición exacta | Cómo se calcula | Umbral objetivo |
|---|---|---|---|
| Calidad / precisión | | | |
| Latencia | | p50 / p95 | |
| Costo | | por consulta | |

## Casos de prueba
| ID | Tipo | Entrada | Salida esperada | Viene de |
|---|---|---|---|---|
| T1 | normal | | | |
| T2 | límite | | | [[Casos difíciles]] |
| T3 | adversarial | | | |

## Cómo se corre
```bash
python eval.py
```

## Resultados
| Fecha | Versión | Métricas | Notas |
|---|---|---|---|
