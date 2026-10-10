---
tags: [problema]
---
# Brief — Reto 2: La caja negra

> [!quote] Brief original
> Descubre cómo se comporta un servicio sin documentación y construye un reemplazo que responda exactamente igual.
>
> Heredamos un servicio que lleva 10 años en producción. Nadie sabe qué hace exactamente. No hay código fuente, no hay documentación y las dos personas que lo escribieron ya no están. Sabemos que recibe mensajes y responde, y que si lo apagamos la empresa se cae. Necesitamos entenderlo por completo y construir un reemplazo que se comporte exactamente igual, incluidos sus errores.

> [!quote] Restricciones
> - No uses herramientas que hagan el trabajo por ti. Scripts y fuzzers propios sí.
> - El reemplazo no puede llamar al original ni a otro reemplazo.
> - Entregables: el reemplazo desplegado, la especificación y el log de experimentos. El formato de los tres está en el README del material.

## Contrato del entrypoint (lo que el set oculto va a usar)
- Desplegado por el equipo, **accesible desde internet desde las 20:00 hasta que termine el demo day**. Hosting libre.
- **Todas** las llamadas llevan `Authorization: Bearer <token>` (token del equipo).
- `GET /health` → `200` cuando el servicio está listo.
- `/*` (URL base) → acepta **exactamente los mismos requests que el original, incluidas las rutas que no existen**.
- `POST /__reset` → vuelve el reemplazo a su estado inicial. **Lo llaman antes de cada test.** Con otro token o sin token, **responde como el original**.

## Entregables
| Hora | Entregable | Formato |
|---|---|---|
| 12:00 | Doc de diseño | una página, PDF o enlace |
| 12:00 | Diagrama de arquitectura | imagen, PDF o enlace |
| 20:00 | Repo | URL pública |
| 20:00 | Entrypoint | URL pública del servicio con `GET /health` + token del equipo |
| 20:00 | Video | enlace público, máx. 2 min |
| 20:00 | Especificación del servicio | formato en README del material |
| 20:00 | Log de experimentos | formato en README del material |
| Antes del turno | Material del pitch | opcional |

## En nuestras palabras
- **Qué tiene que resolver el sistema:** un clon HTTP *conductualmente idéntico* de un servicio con estado, incluidos los errores y las rutas inexistentes, sin acceso a su código.
- **Entrada → salida:** request HTTP (método, ruta, headers, body) → respuesta HTTP (status, headers, body) idéntica a la del original, dado el mismo historial desde el último `/__reset`.
- **Qué significa "funciona":** el set oculto manda secuencias de requests después de un `/__reset` y compara contra el original → ver [[Plan de evaluación]].
- **Dos productos, no uno:** (1) el *conocimiento* (spec + log de experimentos) y (2) el *reemplazo*. El primero alimenta al segundo.

## Material
- [x] **README del material** → `material/README.md`, resumido en [[Reto 2]]
- [x] 20 ejemplos → `material/pruebas/ejemplos.jsonl`, analizados en [[Hallazgos iniciales]]
- [ ] Pestaña **Aclaraciones** de la web

Siguiente: [[Supuestos y alcance]]
