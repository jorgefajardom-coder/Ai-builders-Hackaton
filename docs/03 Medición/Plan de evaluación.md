---
tags: [medicion]
---
# Plan de evaluación

> Fuente única de métricas y objetivos: README → *Plan de Evaluación*. Aquí solo se registran los **resultados**.

## Cómo se corre
```bash
python bench/diff.py                                   # en proceso
python bench/diff.py --target https://caja-negra-production-f95d.up.railway.app
python bench/diff.py --split holdout
```

## Resultados
| Hora | Versión | Objetivo | Casos | Pasos | Notas |
|---|---|---|---|---|---|
| 10:41 | `52f3c9b` | en proceso | 26/26 | 1572/1572 | primer reemplazo completo; hold-out 5/5 |
| 11:04 | `39de677` | Railway | 26/26 | 1572/1572 | contrato del entrypoint 8/8 |
| 11:12 | `eef3bd3` | Railway | 32/32 | 1644/1644 | incluye vueltas del [[Centinela]]; hold-out 8/8 |
| 11:43 | `a2b1a07` | Railway | 47/47 | 1806/1806 | + NOTAS, HALT, antifraude (exp21–23) |
| — | — | `/evento` oficial | —/100 | — | pendiente de validar |
