---
tags: [referencia]
---
# Cronograma

| Hora | Etapa | Entrega / evento | Nota |
|---|---|---|---|
| 10:10–10:30 | Elección de reto | Reto 2 (elegido a las 09:46) | [[Reto 2]] |
| 10:30–**12:00** | Systems design | Doc de diseño de **una página** + diagrama | [[Doc de diseño]] · README del repo |
| 12:00–**20:00** | Ejecución | Repo · entrypoint · video de 2 min · especificación · `experimentos.jsonl` | [[Entrega]] |
| **15:30** | ⚠️ Incidente | El original cambia sin aviso | [[Incidente]] |
| 20:00 | — | Los tokens de participante **dejan de funcionar** contra el original | todo grabado antes |
| 20:00–21:00 | Debrief | 10 min con un juez. El set oculto se corre otra vez sobre la última entrega a tiempo | [[Preguntas probables]] |
| 21:15–22:15 | Demo day | Pitch de 2 min + 2 min de preguntas | [[Pitch]] |
| 22:15–23:00 | Premiación | — | — |

> [!tip] Presupuesto de tiempo de la ejecución (12:00 → 20:00)
> - **12:00–13:00:** esqueleto ASGI desplegado en Railway (`/health`, `/__reset`, 404, 401) + validar en `/evento`
> - **13:00–15:00:** cerrar la fórmula del control; comandos + errores; `diff.py`; validar en `/evento` cada hora
> - **15:00–15:30:** grabar el **corpus de regresión** completo (base para detectar el incidente)
> - **15:30–17:00:** incidente: re-grabar, diff, ajustar; spec sección 6
> - **17:00–18:30:** casos borde y precedencia de errores; spec completa
> - **18:30–19:30:** congelar; re-grabar la regresión contra el original vigente; README + video
> - **19:30–20:00:** entregar todo; verificar el entrypoint desde fuera
