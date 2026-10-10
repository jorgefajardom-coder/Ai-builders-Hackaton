---
tags: [referencia]
---
# Reglas

| | Regla | Implicación práctica |
|---|---|---|
| ✓ | Se pueden y se deben usar modelos y agentes de código. **Se entregan los transcripts y se evalúa cómo los orquestas** | Los transcripts son un entregable más. Hay que trabajar con método: plan → tareas pequeñas → verificar → commit. Pedirle al agente decisiones razonadas, no solo código. Revisar lo que genera. Guardar los transcripts de cada sesión ([[#Transcripts]]) |
| ✗ | No se pueden usar herramientas o proveedores que hagan el trabajo por ti | Sí valen APIs de modelos, librerías y hosting. No valen plataformas que entreguen la solución armada (no-code end-to-end, templates del mismo problema, servicios "AI-app-in-a-box"). Si hay duda, registrarla en [[Decisiones]] con su justificación |
| ✓ | Todo se construye hoy, en un repo público | Commits desde hoy, pequeños y frecuentes, con mensajes claros: el historial es evidencia. Nada de código previo copiado |
| ✓ | Las credenciales son por persona: lo que haces en tu escritorio no lo ve tu compañero | Nunca subir secretos. Cada quien con su `.env` local y un `.env.example` versionado. El servicio desplegado usa los secretos de la plataforma de hosting. La configuración debe permitir que cualquiera lo corra con sus propias llaves |
| ✓ | Presencial y remoto se evalúan con los mismos entregables y los mismos tiempos | Sin ventajas ni excusas: mismo [[Cronograma]] |

## Transcripts
- Una sesión de agente por tarea grande (diseño, esqueleto, evals, iteración, incidente), con nombre claro.
- Al cerrar cada sesión: exportar el transcript y guardarlo en `transcripts/` del repo (o donde indiquen los organizadores).
- Anotar en la bitácora qué sesión resolvió qué cosa.

## Qué evalúa "cómo orquestas" (nuestra lectura)
1. **Contexto:** le das al agente el brief, los supuestos y las restricciones, sin pedirle "hazme todo".
2. **Descomposición:** tareas acotadas y verificables.
3. **Verificación:** corres tests y evals, y no aceptas código a ciegas.
4. **Criterio humano:** las decisiones de diseño las tomas tú; el agente propone alternativas.
5. **Recuperación:** cuando el agente se equivoca, lo detectas y corriges el rumbo.
