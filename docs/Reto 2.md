---
tags: [referencia, reto2]
---
# Reto 2 — Un servicio sin documentación

> [!abstract] Enunciado corto
> Hay que entenderlo por completo y reemplazarlo, **errores incluidos**.
> Brief completo: [[Brief]]

## Entregables extra a las 20:00
- **Especificación** del servicio original → [[Especificación]]
- **Log de experimentos** → [[Log de experimentos]]

## Lectura inicial (antes del brief; se ajusta cuando llegue)
- **"Errores incluidos"** significa que el reemplazo debe ser *compatible incluso en los fallos*: mismos códigos de estado, mismos mensajes y formatos de error, mismos casos borde (y probablemente bugs incluidos). El set oculto casi seguro compara nuestras respuestas con las del original.
- **Cómo lo atacamos:** caja negra con método científico. Cada sondeo al servicio es un experimento: hipótesis → request → observación → regla en la spec.
- **Medición natural:** *paridad*. Mandamos el mismo request al original y al reemplazo y comparamos status, headers relevantes y body. Métrica principal: % de requests con respuesta idéntica, desglosado por endpoint y por tipo (éxito/error).

## Preguntas a resolver con el brief
- [ ] ¿Cómo se accede al servicio original? (URL, binario, contenedor)
- [ ] ¿Protocolo? (HTTP/REST, gRPC, CLI, otro)
- [ ] ¿Tiene estado? (persistencia, sesiones, orden de llamadas)
- [ ] ¿Hay no determinismo? (timestamps, IDs, aleatoriedad, latencia)
- [ ] ¿Qué significa "reemplazarlo"? (mismo contrato, otra URL, despliegue propio)
- [ ] ¿Límites de uso del original? (rate limits, cuotas, disponibilidad después de las 20:00)
