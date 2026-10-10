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
| 14:45 | v1 desplegada | `/evento` oficial 1/3 | **87/100** | — | fáciles 40/40 · regulares 36/40 · difíciles 11/20; hipótesis (no verificable): el set ya esperaba v2 |
| 16:05 | v1 desplegada | `/evento` oficial 2/3 | **87/100** | — | mismo desglose; 9 por status, 4 por cuerpo, 1 en el primer request |
| 16:26 | `0b8ffbf` (v2) | `/evento` oficial 3/3 | **90/100** | — | fáciles 39/40 · regulares 36/40 · difíciles 15/20; **posible** contaminación, no confirmada: nuestro diff contra Railway corrió en paralelo (16:25–16:30) con el mismo token |
| 16:54 | `6044d15` | en proceso + Railway | 340/340 · Railway 9/9 (exp32–35, fz2-001) | 5008/5008 | fuzzer diferencial: semilla 2 → 59/60 (halló CT-15, mismo titular sin límite); semilla 3 → **40/40** tras el fix |
| >20:00 | último entrypoint | corrida final del jurado | —/100 | — | **la que cuenta**; nadie debe usar el token del equipo después de las 20:00 |
