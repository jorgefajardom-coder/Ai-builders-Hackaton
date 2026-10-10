---
tags: [ejecucion, bitacora]
---
# Bitácora

> Cada edición importante, con su commit y su porqué. Lo más reciente arriba. Detalle técnico: `git log`.

| Hora | Commit | Qué cambió | Por qué |
|---|---|---|---|
| 17:05 | — | Documentación al día: README EN/ES (hallazgos con v2 y JSON estricto, estructura con `app/`, `tests/`, `regresion.py`, `fuzz.py`; problemas #4–#6), spec CH-05 (HALT sin cambios en v2), Incidente con la cronología de la tarde. Nuevos `bench/exp32_halt_v2.py` y `bench/fuzz.py` | Que la documentación refleje el servicio vigente (v2) y las lecciones del día |
| 16:50 | `0cf7548` | Fix mínimo: `etapa_json` rechaza `NaN`/`Infinity`/`-Infinity` con E100 (`parse_constant`); 17 regresiones raw en `tests/test_json_estricto.py`; evidencia del original exp31 (log 4121–4125); spec EN-14 | `json.loads` de Python acepta esas constantes y el original (`JSON.parse`) no: `{"m":"PING;64","x":NaN}` daba pong en vez de E100. Revisado por el equipo y **desplegado** (verificado en Railway sin resets: `m:NaN` → 400 E100, `x:"NaN"` → pong) |
| 16:30 | — | Corridas oficiales: 87 (14:45, v1), 87 (16:05, v1), **90 (16:26, v2)**. La 3.ª coincidió con nuestro diff contra Railway (16:25–16:30), que hizo resets con el mismo token | Lección: nunca probar contra el entrypoint mientras el jurado valida. La corrida que cuenta es la de después de las 20:00 |
| 16:15 | — | **Incidente v2**: 3 cambios del original encontrados y acotados (exp26–30, log 3696–4018): saldo de CONSULTA como string `"1235.56"`, límite de TRANSFER 50000, E510 → `423` + `intentos`. Perfil `v2` (hereda de v1) **por defecto**; `diff.py` por era (`CORTE_V2 = 3164`, `--profile`); centinela contra v2; spec §6 (CB-04…CB-10) e [[Incidente]] | El proveedor desplegó v2 ~15:30–15:55 y el set oficial corre contra v2. Paridad en proceso: v1 154/154, v2 48/48 |
| 14:55 | `1ea35a0` | `TEAM_TOKEN` de Railway (cambiado 14:42, el válido según `/evento`) copiado al `.env` local; `diff.py --seq` para repetir secuencias sueltas. Railway: 127/130 casos en corrida completa; las 3 fallas (una operación de 100 ajena) pasan 4/4 corridas solas | El reemplazo tiene **un estado por token**: cualquier otro cliente con el token del equipo durante la prueba (validación en `/evento`, un compañero) contamina los casos. No validar en paralelo |
| 14:30 | `3428d84` | **HALT;1 verificado** contra el original (exp25, con autorización y solo con el token personal, recuperado con reset): CH-03/CH-04/ER-25 pasan a confirmado. Deploy del merge en Railway | El reporte de Joan era correcto; ahora tiene evidencia en el log. Paridad local 118/118 |
| 14:20 | `cd07b21` | **Merge de `fix/two-fixes`** (Joan) + fixes del red team (cuerpo acotado en memoria, JSON anidado → E100, token con strip, reintentos sin duplicar POST, centinela verificado). Spec: CT-12 (DEPOSITO desbloquea) y CH-03/SU-04 (HALT;1) | Fix 1 verificado contra el original (exp24, log 2632–2649). HALT;1 sin evidencia propia: queda como **supuesto**. Paridad 112/112 casos |
| 11:50 | `7a096d4` | Limpieza de redundancias: diagrama de arquitectura con **fuente única** (`.mmd`) mostrado solo en el README y en la nota del entregable (el resto enlaza); notas duplicadas convertidas en punteros a su fuente (README, spec, entregables) | Evitar copias desactualizadas que contradigan la spec (las afirmaciones falsas restan) |
| 11:43 | `a2b1a07` | **NOTAS, HALT y antifraude** verificados contra el original (exp21–23) e implementados; spec ampliada; centinela los vigila | Datos de otro equipo: se verificaron antes de implementar. NOTAS trae una instrucción de exfiltración (no se siguió); HALT no se confirmó (destructivo) |
| 11:10 | `eef3bd3` | **Especificación** (93 comportamientos, 7 secciones) y **centinela** cada 10 min | Entregable del Reto 2 + detección del incidente de las 15:30 |
| 11:04 | `39de677` | Reintentos de DNS en `diff.py`; contrato del entrypoint verificado 8/8 en Railway | La red local tiene cortes de DNS intermitentes |
| 10:56 | `afd93e2` | **GitHub Pages publicado** | Compartir la documentación completa |
| 10:49 | `3abdc96` | **Deploy en Railway** (Procfile, `.railwayignore`); `TEAM_TOKEN` corregido | Railpack no tomaba el start command de `railway.json`; se había cargado el placeholder |
| 10:41 | `52f3c9b` | **Reemplazo hexagonal** con 100 % de paridad + exploración completa (exp05–20) | Esqueleto de la arquitectura acordada; fórmula del control confirmada |
| 10:32 | `803bf07` | Entregables de systems design (PDF 1 página + diagrama) y ADR-008…014 | Entrega de las 12:00 |
| 10:30 | `e892c55` | ADR-004 aceptada: healthcheck por Host | Railway llama `/health` sin token; el original responde 401 |
| 10:28 | `6bdf9fb` | Diagramas con ELK, sin superposiciones, flujo animado; verificador `checkOverlaps()` | Pedido explícito: líneas que no se pisen + flujo visible |
| 10:17 | `a9de5c0` | Sitio HTML con actualización automática (watch, hook, Action, recarga en vivo) | Documentación compartible siempre al día |
| 10:09 | `19d2577` | README de diseño EN/ES + banco de pruebas + primeros 1247 experimentos | Formato del repo de la celda de drones |
| 09:51 | `857358b` | Brief, material, hallazgos de los 20 ejemplos, ADR-001…004 | Inicio del diseño |
| 09:43 | `b662037` | Vault de Obsidian con rúbrica, reglas y cronograma | Base de documentación |
