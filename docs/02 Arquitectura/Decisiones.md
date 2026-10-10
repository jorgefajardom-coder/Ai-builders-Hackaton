---
tags: [arquitectura, moc]
---
# Registro de decisiones

> [!tip] Regla de la rúbrica
> Cada decisión dice qué alternativa descartó y por qué. Para una decisión nueva, crea una nota en `Decisiones/` con la plantilla [[Plantillas/Decisión]].

| ID | Decisión | Elegido | Descartado | Estado |
|---|---|---|---|---|
| [[ADR-001]] | Stack del reemplazo y control de la respuesta HTTP | Catch-all de bajo nivel (por definir lenguaje) | Routing declarativo de framework (FastAPI/Express) | propuesta |
| [[ADR-002]] | Dónde vive el estado | Memoria, 1 instancia, snapshot inicial | Base de datos (Redis/Postgres/SQLite) | propuesta |
| [[ADR-003]] | Cómo descubrimos y verificamos el comportamiento | Corpus grabado + tester diferencial | Exploración manual con curl/Postman; leer y adivinar | propuesta |
| [[ADR-004]] | Hosting | Por decidir (siempre encendido, sin cold start) | Plataformas con suspensión por inactividad | propuesta |
