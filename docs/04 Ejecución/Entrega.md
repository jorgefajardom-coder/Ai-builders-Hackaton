---
tags: [ejecucion]
entrega: "20:00"
---
# Entrega — 20:00

- [x] **Repo público** — github.com/jorgefajardom-coder/Ai-builders-Hackaton (público)
- [x] **Servicio desplegado** y probado desde una máquina/red distinta — Railway (URL abajo)
- [x] Entrypoint claro y documentado en el README — sección *Entrypoint Contract* / *Contrato del Entrypoint* y bloque de abajo
- [x] Corre contra el set de evaluaciones oculto (formato de entrada/salida verificado)
- [x] **Video de 2 minutos** → https://youtu.be/oBzgzodlFgU
- [x] Resultados del [[Plan de evaluación]] actualizados — paridad local por era
- [ ] **Transcripts** de las sesiones con agentes → [[Reglas#Transcripts]]
- [x] Sin secretos en el repo; `.env.example` presente — `.env` en `.gitignore`; escaneo del repo sin tokens
- [x] *(Reto 2)* Especificación — `spec/ESPECIFICACION.md`
- [x] *(Reto 2)* [[Log de experimentos]] — `experimentos.jsonl`

## Entrypoint
```bash
# Procfile (Railway); en local: TEAM_TOKEN=... y PORT opcional (8000 por defecto)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-server-header --no-access-log
```
Perfil por defecto `v2` (vigente); `BEHAVIOR_PROFILE=v1` reproduce la mañana.

## URL del servicio
https://caja-negra-production-f95d.up.railway.app

## Video
[![Video demo](https://img.youtube.com/vi/oBzgzodlFgU/hqdefault.jpg)](https://youtu.be/oBzgzodlFgU)

https://youtu.be/oBzgzodlFgU

Guion y prompt: [[Prompt video]].
