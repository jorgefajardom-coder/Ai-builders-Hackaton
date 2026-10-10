# Diagrama de arquitectura — Caja Negra

![Diagrama de arquitectura](diagrama-arquitectura.png)

Renderizado: `diagrama-arquitectura.png` / `diagrama-arquitectura.svg` (fuente: `diagrama-arquitectura.mmd`, Mermaid + ELK).

**Lectura (de arriba abajo):**
- **A · Descubrimiento** — único componente que habla con el original (token personal, 10 req/s). Cada request queda en el log con su hipótesis.
- **Conocimiento** — único puente entre A y B: `experimentos.jsonl` → ajuste + validación predictiva → especificación; y el corpus de regresión (dev / hold-out con otra semilla).
- **Medición** — el tester diferencial reproduce el corpus contra el reemplazo con el comparador del jurado; el set oculto entra por el mismo adaptador.
- **B · Reemplazo (hexagonal)** — adaptador HTTP (borde) → pipeline ordenado de validación guiado por el **catálogo de errores** (datos) → **registro de comandos** (un módulo por comando) → **núcleo de dominio puro** → **puerto StateStore** (InMemory activo; Redis opcional). El **perfil de comportamiento** (`BEHAVIOR_PROFILE`) selecciona catálogo y comandos: así se absorbe el cambio de las 15:30 sin tocar el núcleo.
- Flecha gruesa = camino crítico de cada request. Discontinuo = adaptador posible, no desplegado.

```mermaid
---
config:
  layout: elk
  elk:
    nodePlacementStrategy: BRANDES_KOEPF
  flowchart:
    curve: linear
    wrappingWidth: 340
    subGraphTitleMargin:
      top: 6
      bottom: 14
---
flowchart TB
    ORIG[("Servicio original<br/>Railway · estado por token")]

    subgraph A["A · Descubrimiento"]
        direction TB
        EXP["Experimentos exp01…expNN<br/>1 hipótesis por request"]
        PRB["prober.py<br/>reset → secuencia → registro<br/>10 req/s · reintentos"]
        EXP --> PRB
    end

    subgraph K["Conocimiento · git"]
        direction TB
        LOG[("experimentos.jsonl<br/>formato oficial")]
        FIT["Ajuste + validación predictiva<br/>fit_*.py · control_model.py"]
        SPEC["ESPECIFICACION.md<br/>ID · evidencia · confianza"]
        CORP[("Corpus de regresión<br/>dev · hold-out (otra semilla)")]
        LOG --> FIT --> SPEC
        LOG --> CORP
    end

    DIFF["Tester diferencial<br/>comparador del jurado → paridad %"]
    JUDGE["Set oculto del jurado<br/>100 tests · token del equipo"]

    subgraph B["B · Reemplazo"]
        direction TB
        HTTP[["Adaptador HTTP · ASGI catch-all<br/>sin framework · nunca llama al original"]]
        PIPE["Pipeline de validación ordenado<br/>ruta → auth → forma del cuerpo → control<br/>→ sintaxis/aridad → existencia → negocio"]
        CAT[("Catálogo de errores<br/>código · status · cuerpo exacto · etapa")]
        PROF["Perfil de comportamiento<br/>BEHAVIOR_PROFILE = v1 | v2<br/>base común + overrides"]
        REG["Registro de comandos<br/>ALTA · CONSULTA · DEPOSITO<br/>TRANSFER · ANULA · PING"]
        DOM["Núcleo de dominio<br/>funciones puras (estado, cmd) → (estado', resp)"]
        IDS["Generadores de IDs<br/>AC-0001 · OP-0001 deterministas"]
        PORT{{"Puerto StateStore<br/>get · apply · snapshot · reset"}}
        MEM[("InMemoryStore<br/>activo · 1 proceso / 1 réplica")]
        RED[("RedisStore<br/>opcional · partición por token")]
        HTTP ==> PIPE
        PIPE --> REG
        REG --> DOM
        DOM --> PORT
        PORT --> MEM
        PORT -.-> RED
        PROF --> CAT
        CAT --> PIPE
        PROF --> REG
        IDS --> DOM
    end

    PRB -->|"HTTPS · token personal"| ORIG
    PRB --> LOG
    CORP --> DIFF
    DIFF --> HTTP
    JUDGE --> HTTP

    classDef orig fill:#8b0000,stroke:#5a0000,color:#fff
    classDef bench fill:#378ADD,stroke:#042C53,color:#fff
    classDef know fill:#534AB7,stroke:#26215C,color:#fff
    classDef data fill:#4a4a4a,stroke:#2a2a2a,color:#fff
    classDef app fill:#1D9E75,stroke:#085041,color:#fff
    classDef cfg fill:#C98A1B,stroke:#6B4700,color:#fff
    classDef store fill:#1a5c2a,stroke:#0d3315,color:#fff
    classDef opt fill:#ffffff,stroke:#1a5c2a,color:#1a5c2a,stroke-dasharray: 5 5
    classDef meas fill:#B75A34,stroke:#5C2506,color:#fff
    class ORIG orig
    class EXP,PRB bench
    class FIT,SPEC know
    class LOG,CORP data
    class HTTP,PIPE,REG,DOM,IDS app
    class CAT,PROF cfg
    class PORT,MEM store
    class RED opt
    class DIFF,JUDGE meas
```
