---
tags: [arquitectura]
---
# Arquitectura

## Diagrama
```mermaid
flowchart LR
    U[Usuario / Entrada] --> E[Entrypoint]
    E --> P[Procesamiento]
    P --> M[(Modelo / LLM)]
    P --> O[Salida]
```

## Componentes
| Componente | Responsabilidad | Tecnología | Decisión |
|---|---|---|---|
| Entrypoint | | | [[ADR-001]] |

## Flujo de datos
1.

Todas las decisiones: [[Decisiones]]
