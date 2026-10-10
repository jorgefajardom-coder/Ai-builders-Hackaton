---
tags: [arquitectura, investigación]
fecha: 2026-10-10
estado: propuesta
---
# Investigación de arquitecturas

> [!summary] Para qué sirve esta nota
> Revisa patrones conocidos para **reemplazar un sistema legado de caja negra** y para **construir el reemplazo como un motor de reglas modular**. Cada área dice qué elegimos, qué descartamos y por qué, con fuentes. Alimenta [[Decisiones]] y [[Arquitectura]]. Va pensada para **8 horas de construcción**: lo que sobra se marca como **overkill**.

---

## 0 · Recomendación ejecutiva

### La arquitectura objetivo en 10 puntos

1. **Hexagonal (puertos y adaptadores) en 5 capas:** borde HTTP → aplicación → dominio puro → puertos → adaptadores de estado. Las dependencias apuntan siempre hacia el dominio. El dominio no importa nada de HTTP ni de uvicorn.
2. **Borde HTTP = catch-all ASGI puro** sobre `uvicorn --workers 1`. Un solo `async def app(scope, receive, send)` recibe cualquier método y ruta. Ningún framework responde por nosotros: ni 404, ni 405, ni 422, ni redirects de `/` final. Se mantiene [[ADR-001]].
3. **Pipeline de validación con precedencia explícita** (cadena de responsabilidad). Las etapas son `ruta → auth → cuerpo → integridad → sintaxis → existencia → negocio`. Cada etapa devuelve `Ok(ctx)` o `Err(código)`, y **el orden lo da una lista del perfil**, no el anidado de `if`s. Así, cambiar la precedencia entre E202 y E302 es cambiar una línea de datos.
4. **Registro de comandos (patrón Command + registry):** `ALTA`, `CONSULTA`, `DEPOSITO`, `TRANSFER`, `ANULA` y `PING` son clases o funciones con la misma firma `(args, estado, ids) → Resultado`. Se registran en un diccionario `{nombre: handler}` con su aridad declarada. Un comando nuevo después de las 15:30 es **un archivo más**, sin tocar el dispatcher.
5. **Dominio puro y determinista:** los handlers son funciones **síncronas** sin I/O, sin reloj y sin aleatoriedad. Reciben el estado y devuelven `(nuevo_estado, respuesta)`. El valor de control (ISO 7064 mod 97-10) vive en `checkval.py`, que es el mismo código que valida el banco de pruebas (ADR-005).
6. **Catálogo de errores como datos:** `errors.py` (o un YAML del perfil) guarda `{código: (status, cuerpo exacto)}`. Los handlers solo lanzan `DomainError("E401")` y el borde HTTP lo traduce. Ningún string de error aparece suelto en el código.
7. **Perfiles de comportamiento versionados:** `profiles/v1_manana.py` y `profiles/v2_incidente.py` declaran el catálogo de errores, el orden del pipeline, los límites (montos, aridades), el algoritmo de control y los *overrides* de comandos. La variable `BEHAVIOR_PROFILE` elige uno, y por defecto rige el vigente a las 20:00. El incidente de las 15:30 se modela como un **perfil nuevo que hereda del anterior y solo sobrescribe lo que cambió**. El diff entre perfiles es, literalmente, la sección 6 de la spec.
8. **Puerto `StateRepository` + `IdGenerator`**, con el estado **particionado por token**. Hoy el adaptador es `InMemoryRepository`: un `dict[token, Ledger]` con una *factory* del estado inicial, y `/__reset` llama `factory()` (más barato y seguro que `deepcopy`). Los IDs de cuentas y operaciones salen de contadores **dentro del estado**, así que el reset también los reinicia. Un adaptador Redis o Postgres queda **documentado, no construido**.
9. **Despliegue: Railway, 1 réplica, *Serverless* apagado, healthcheck en `/health`, `uvicorn --workers 1 --no-server-header`.** La escalabilidad horizontal se defiende *en principio* (app sin estado + repositorio enchufable) y **se renuncia a ella a propósito** en el despliegue, porque el evaluador habla con un solo proceso ([[ADR-002]]).
10. **Red de seguridad = tester diferencial + golden files + CI:** el corpus `experimentos.jsonl`, marcado por versión del servicio, se reproduce contra el reemplazo con el **mismo comparador del jurado**. Corre en un hook pre-push o en GitHub Actions. Los logs son JSON, una línea por request (`seq`, `cmd`, `etapa_que_cortó`, `código`, `ms`). El `/health` confirma el perfil activo solo por log, nunca en el cuerpo, porque el cuerpo se compara.

### Diagrama de componentes (reemplazo)

Las capas van de arriba abajo. Cada flecha solo baja una capa y ninguna cruza otra. La línea punteada es un adaptador futuro, no construido.

> Esta recomendación se adoptó con ajustes; el diagrama vigente es [[diagrama-arquitectura]] (fuente única).

### Diagrama de la red de seguridad (banco + CI)

> El flujo de descubrimiento está en el README → *Ciclo de Descubrimiento* (fuente única).

---

## 1 · Patrones para reemplazar un sistema legado de caja negra

| Patrón | Qué es | ¿Aplica aquí? | Veredicto |
|---|---|---|---|
| **Strangler Fig** | Poner una fachada delante del legado y redirigir rutas al sistema nuevo una por una hasta "estrangular" el viejo ([Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html)) | No hay migración gradual: el jurado habla **solo** con el reemplazo, y el reemplazo **no puede llamar** al original | **Descartado** como mecanismo. Lo citamos como el patrón "de producción" que usaríamos fuera del reto |
| **Parallel run / shadow traffic** | Mandar el mismo tráfico a viejo y nuevo y comparar: [GitHub Scientist](https://github.com/github/scientist), [Twitter Diffy](https://github.com/opendiffy/diffy), [GoReplay](https://github.com/buger/goreplay) | El reemplazo no puede llamar al original. Pero **el banco de pruebas sí puede** mandar la misma secuencia a ambos | **Adoptado en versión offline:** `diff.py` repite cada secuencia grabada contra el reemplazo. Es Scientist con el "control" grabado en vez de vivo |
| **Characterization / golden master / approval testing** | Fijar con tests lo que el sistema *hace hoy*, no lo que "debería" hacer (Feathers, *Working Effectively with Legacy Code*; [ApprovalTests](https://approvaltests.com/)) | Es exactamente el criterio del jurado: igualar status y cuerpo, errores incluidos | **Adoptado:** cada línea del log es un golden. Se congelan en `golden/<perfil>.jsonl` |
| **Differential testing** | Dos implementaciones, misma entrada, comparar salidas ([McKeeman 1998](https://www.cs.dartmouth.edu/~mckeeman/references/DifferentialTestingForSoftware.pdf)) | Es el núcleo de [[ADR-003]] | **Adoptado** (ya aplicado) |
| **Record / replay** | Grabar el tráfico y reproducirlo (VCR.py, GoReplay) | Útil como test, **inútil como implementación**: no generaliza a entradas ni estados nuevos | **Adoptado solo como test.** Como reemplazo, descartado ([[ADR-001]]) |
| **Contract testing (Pact)** | El consumidor publica expectativas y el proveedor las verifica ([docs.pact.io](https://docs.pact.io/)) | Supone un consumidor conocido y negociación de contrato. Aquí el "contrato" es el comportamiento observado | **Overkill.** Nuestro corpus JSONL ya *es* el contrato, sin el broker |
| **Model-based / property-based (Hypothesis stateful)** | Una máquina de estados genera secuencias de comandos y compara contra un modelo ([Hypothesis stateful](https://hypothesis.readthedocs.io/en/latest/stateful.html)) | Muy útil **contra nuestro propio reemplazo** para invariantes: el saldo nunca es negativo, `ANULA` deshace `TRANSFER`, `reset` deja todo igual, aridad × control | **Adoptado parcialmente, después de las 17:00 si sobra tiempo.** Contra el original no: consume el presupuesto de requests y no deja hipótesis por línea |
| **Inferencia de autómatas (L\*, LearnLib)** | Aprender activamente una máquina de Mealy con *membership* y *equivalence queries* ([Angluin 1987](https://doi.org/10.1016/0890-5401(87)90052-6), [LearnLib](https://learnlib.de/)) | El espacio de entrada es enorme (montos, IDs, control) y la máquina depende de datos, no es de estados finitos chica. Necesita JVM y abstracción de alfabeto | **Overkill para 8 h.** Tomamos la idea: un alfabeto abstracto de comandos (`ALTA_ok`, `DEP_ok`, `DEP_sin_saldo`…) para diseñar secuencias |
| **Fuzzing basado en gramáticas** | Generar entradas desde una gramática del protocolo ([The Fuzzing Book](https://www.fuzzingbook.org/html/Grammars.html)) | El formato `CMD;args;CONTROL` es una gramática trivial. Generar mensajes **con control válido** es clave para pasar la barrera E201/E202 | **Adoptado, liviano:** un generador propio de ~40 líneas que arma `CMD;args` y calcula el control con `checkval.py`. Mutaciones dirigidas: control ±1, aridad ±1, montos frontera |

**Lo que elegimos:** *characterization + differential offline + gramática liviana*.
**Lo que descartamos:** Strangler Fig y shadow traffic en vivo (prohibido llamar al original), Pact (sin consumidor real), L\*/LearnLib (costo de montaje frente a 8 h).

---

## 2 · El reemplazo como motor de reglas modular

### 2.1 Estructura: hexagonal

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **Hexagonal / puertos y adaptadores** ([Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)) | El dominio se prueba sin HTTP; el estado se cambia de adaptador sin tocar reglas; las fronteras son defendibles en el debrief | Algo más de archivos | **Elegido**, en versión mínima: 2 puertos (`StateRepository`, `IdGenerator`) |
| Clean Architecture completa (use cases, presenters, DTOs por capa) | Ortodoxa | Ceremonia sin beneficio en un servicio de 6 comandos | **Descartado (overkill)** |
| Un solo `app.py` con `if/elif` | Rápido de escribir | La precedencia de errores queda implícita en el anidado; el incidente obliga a reescribir | **Descartado**: es el anti-patrón que el pipeline resuelve |

### 2.2 Validación: pipeline con precedencia explícita

- **Patrón:** cadena de responsabilidad ([refactoring.guru](https://refactoring.guru/design-patterns/chain-of-responsibility)) en su forma funcional: `STAGES = [route, auth, body, control_format, control_value, syntax, existence, business]`. Se recorre la lista y **gana el primer error**.
- **Por qué importa:** el jurado tiene casos de *dos defectos por mensaje* (ver [[Plan de evaluación]]). La precedencia observada (E404 antes de E001, control antes de aridad) es justo lo que el incidente puede cambiar. Si el orden es una lista del perfil, el cambio es un *diff* de una línea, auditable y citado en la spec.
- **Descartado:** validación declarativa con Pydantic. Valida todo el modelo, acumula errores y su orden no es el nuestro. Además genera 422 propios ([FastAPI · handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)).

### 2.3 Comandos: Command + registry

```python
@command("TRANSFER", arity=3)
def transfer(args, st: Ledger, ids: IdGenerator) -> Result: ...
```
- El `registry` resuelve el nombre, chequea aridad (E301/E302) y despacha.
- **Descartado:** jerarquías de clases con herencia profunda. Con funciones registradas alcanza, y es más fácil sobrescribir una en un perfil.

### 2.4 Perfiles de comportamiento (versionado)

| Opción | Veredicto |
|---|---|
| **Perfil como módulo Python que hereda del anterior** (`V2 = V1.override(errors={...}, stages=[...], commands={"ANULA": anula_v2})`) | **Elegido.** Es tipado, ejecutable y el diff es legible |
| Perfil 100 % YAML / JSON | Descartado: el algoritmo de control y la lógica de un comando no son datos. Usaríamos YAML solo para el catálogo de errores si crece |
| *Feature flags* sueltos (`if INCIDENT:`) | Descartado: se esparcen por el código y no dejan una lista cerrada de "qué cambió" |
| Rama git por versión | Descartado: duplica el código y no permite correr el diferencial de **ambas** versiones en el mismo CI |

**Regla operativa:** el corpus se marca con `version` según la hora del request (antes o después de las 15:30, confirmado por diff). `diff.py --profile v1` compara contra goldens v1 y `--profile v2` contra v2. Desplegamos con `BEHAVIOR_PROFILE=v2`.

### 2.5 Catálogo de errores como datos

- `errors.py`: `CATALOG = {"E001": (401, {"error": "E001", "mensaje": "no autorizado"}), ...}`.
- Los handlers lanzan `DomainError(code)` y solo el borde arma la respuesta. **Un único lugar** para cada string exacto; la spec (sección 5) se genera o verifica desde este dict.

### 2.6 Determinismo e IDs

- Los contadores de cuenta y de operación viven **dentro del `Ledger`**, nunca como globales del módulo. Así `/__reset` los devuelve al inicio sin código extra.
- Prohibido `uuid4`, `random` y `time.time()` en el dominio. Si el original muestra fechas o IDs aleatorios, se inyecta un puerto `Clock` o `Rng` con semilla fija y se anota como `supuesto`.
- El reset usa `state_factory()` en vez de `deepcopy(snapshot)`. Es más rápido, no comparte referencias por accidente y obliga a escribir el estado inicial de forma explícita.

### 2.7 Concurrencia

- Uvicorn corre **un** event loop. Si los handlers del dominio son **síncronos** y no hay `await` entre leer y escribir el estado, cada request es atómico sin lock. Dejamos un `asyncio.Lock` de todos modos: cuesta casi nada y protege si alguien agrega un `await`.
- **Descartado:** `threading.Lock` con un servidor en hilos. No aplica a ASGI.

---

## 3 · Escalabilidad bien hecha (y por qué no la desplegamos)

> [!warning] El trade-off, dicho sin rodeos
> El set oculto le habla a **un solo proceso** y "si tu plataforma levanta varias instancias, cada una tendrá su propio estado". Escalar horizontalmente con estado local **rompe la paridad**. Por eso diseñamos para escalar y desplegamos sin escalar.

| Pieza | Cómo escalaría en producción | Qué hacemos hoy |
|---|---|---|
| App | Sin estado: toda la memoria pasa por `StateRepository` | Igual: el código ya no guarda estado fuera del repositorio |
| Estado | `RedisRepository`: un `HASH` por token, operaciones con `WATCH/MULTI` o script Lua para que `TRANSFER` sea atómico. O `PostgresRepository` con `SELECT … FOR UPDATE` y una fila por token ([Redis transactions](https://redis.io/docs/latest/develop/interact/transactions/)) | `InMemoryRepository`. El Redis queda como interfaz y nota de diseño, **no construido** |
| Partición | **Por token** (cada token es un *tenant* aislado, como en el original). Permite *sharding* por hash del token y sticky routing | `dict[token, Ledger]`. Solo el token del equipo pasa auth, pero la partición es gratis y refleja el original |
| Idempotencia | Clave de idempotencia por request para reintentos seguros en `DEPOSITO`/`TRANSFER` | **No se implementa:** el original no la tiene y agregarla cambiaría respuestas. Va a la sección 7 (Riesgos) de la spec como recomendación |
| Réplicas | N réplicas detrás del balanceador + estado compartido | **1 réplica, 1 worker**, fijado en `railway.json` |

**Por qué no Redis hoy:** agrega latencia de red, un servicio extra que puede caerse dentro de la ventana de 5 s y un punto de no-paridad en el reset, sin ningún test que lo premie. **El costo de renunciar:** el reemplazo no sobrevive a un reinicio con estado. Es aceptable, porque cada test empieza con `/__reset`.

---

## 4 · Núcleo HTTP en Python

| Opción | Comportamientos por defecto que rompen la paridad | Veredicto |
|---|---|---|
| **ASGI crudo sobre uvicorn** | Casi ninguno. Uvicorn solo responde por su cuenta ante **HTTP malformado** (400 en texto plano) y en errores no capturados (500 `Internal Server Error`) ([uvicorn · server behavior](https://uvicorn.dev/server-behavior/)) | **Elegido.** Hay que envolver la app con un `try/except` que devuelva el error del original en vez del 500 de uvicorn |
| Starlette | `Router` responde 404 `Not Found` en texto plano y 405 propios; `redirect_slashes=True` redirige `/msg/` → `/msg` con 307 ([Starlette routing](https://www.starlette.io/routing/)) | Aceptable **solo** con un `Mount`/ruta catch-all. Aporta poco frente a ASGI crudo |
| FastAPI | Todo lo de Starlette más **422 automáticos** de validación con su propio JSON, `/docs`, `/openapi.json` y `/redoc` expuestos (¡rutas que deberían dar E404!), y `HEAD`/`OPTIONS` implícitos | **Descartado** |
| aiohttp low-level (`web.Server(handler)`) | Bajo nivel y controlable; pero es otro servidor y otra API que aprender | Descartado: no gana nada sobre ASGI + uvicorn |
| stdlib `http.server` | Hilos; respuestas de error HTML propias (`send_error`) para métodos desconocidos (501) | Descartado: frágil y lento de endurecer |

**Settings de uvicorn:** `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1 --no-server-header --proxy-headers --timeout-keep-alive 5`. Los headers no se comparan, pero `--no-server-header` evita filtrar el stack. **Nunca** `--reload` ni `--workers > 1`.

**Detalles que hay que cuidar en el borde:**
- Leer el body completo hasta `more_body=False` antes de decidir.
- **Distinguir** body vacío, no-JSON, JSON sin `m` y `m` no-string. Cada uno puede tener un error distinto en el original: hay que sondearlos.
- Serializar con `json.dumps(obj, ensure_ascii=False, separators=…)` igual al original **solo si** alguna respuesta no fuera JSON. Para JSON, el comparador ignora el orden de las claves.
- Rutas: comparación exacta de `scope["path"]` (sensible a mayúsculas y a `/` final, ya confirmado) y del método.

### Railway

| Ajuste | Valor | Por qué / fuente |
|---|---|---|
| Serverless (App Sleeping) | **Apagado** | Con *Serverless*, el servicio se duerme tras 10 min sin tráfico **saliente** y la primera request puede devolver **502** ([Railway · Serverless](https://docs.railway.com/reference/app-sleeping)) |
| Réplicas | **1** | Varias réplicas = varios estados ([Railway · scaling](https://docs.railway.com/reference/scaling)) |
| Healthcheck path | `/health` | Railway lo consulta **solo durante el deploy** y exige un **2xx**. Lo llama **sin token**, desde el hostname `healthcheck.railway.app` ([Railway · healthchecks](https://docs.railway.com/guides/healthchecks)). Nuestro `/health` sin token responde 401 (E001), igual que el original, así que el deploy fallaría. **Decisión:** en el borde, `GET /health` con `Host: healthcheck.railway.app` responde 200 `{"ok":true}`. El jurado nunca usa ese Host, así que la paridad no cambia. Gracias a esto el deploy no corta el servicio. Se anota como `supuesto` en Riesgos. **Alternativa más simple:** no configurar el healthcheck y validar a mano con el token tras cada deploy |
| Config as code | `railway.json` con `startCommand`, `numReplicas: 1`, `sleepApplication: false` | Reproducible y revisable en el repo |
| Variables | `TEAM_TOKEN`, `BEHAVIOR_PROFILE`, `LOG_LEVEL` | Nada sensible en el código |

> [!danger] Trampa del healthcheck
> No agregar una ruta como `/healthz` para Railway. El original responde **E404** a toda ruta desconocida, y el set "incluye rutas que no existen". Una ruta extra es un test perdido si el jurado la prueba.

---

## 5 · Observabilidad y red de seguridad para un build de 1 día

| Herramienta | Qué hacemos | Overkill |
|---|---|---|
| **Logging estructurado** | Una línea JSON por request desde el borde: `{ts, method, path, cmd, stage_failed, code, status, ms, profile}`. Sin el token ni el cuerpo completo | OpenTelemetry, Prometheus, dashboards |
| **Golden files** | `golden/v1.jsonl` y `golden/v2.jsonl` congelados desde el log; se regeneran solo a propósito | Snapshot testing con librerías externas |
| **Diferencial en CI** | `python bench/diff.py --target local --profile v2` en un hook pre-push (ya existe `tools/install_hooks.py`) y opcionalmente GitHub Actions. Falla si la paridad baja respecto del último commit | Matriz de versiones de Python, contenedores de test |
| **Smoke del deploy** | Tras cada deploy: `diff.py --target $URL` con 10 secuencias rápidas | Monitoreo sintético continuo |
| **Tests de propiedades** | Hypothesis stateful contra el dominio puro (sin HTTP): invariantes de saldo, reset idempotente | Mutation testing |
| **Detección del incidente** | A las 15:30+ re-correr un set fijo de "secuencias centinela" (~30 requests) y comparar contra `golden/v1`. Cada diferencia es una fila de la sección 6 de la spec | Detección continua por cron |

---

## 6 · Qué es overkill para 8 horas (resumen)

- LearnLib / L\* automático, Pact broker, Clean Architecture completa.
- Construir el `RedisRepository` (basta la interfaz y la nota).
- OpenTelemetry, métricas Prometheus, autoscaling.
- Un DSL propio de reglas o un motor de reglas genérico (Drools-like): 6 comandos no lo justifican. El "motor" es la lista de etapas más el registro.
- LLM dentro del reemplazo: permitido por las reglas, pero no determinista y con latencia. Ya está descartado en ADR-006.

---

## 7 · Cambios propuestos a las ADRs

| ID | Decisión | Elegido | Descartado | Por qué |
|---|---|---|---|---|
| ADR-001 (enmienda) | Núcleo HTTP | ASGI crudo + uvicorn `--workers 1 --no-server-header` + `try/except` global que mapea excepciones al error del original | FastAPI (422, `/docs` y `/openapi.json` expuestos), Starlette Router (404/405 en texto plano, redirect de `/` final), aiohttp, `http.server` | Cada default del framework es una respuesta que no controlamos en las categorías que el set prueba |
| ADR-002 (enmienda) | Estado | `StateRepository` con `InMemoryRepository`, particionado por token, reset por `factory()`, IDs dentro del estado | Redis/Postgres desplegado; `deepcopy` de snapshot; contadores globales | Diseño listo para escalar sin pagar latencia ni riesgo hoy; el reset reinicia también los IDs |
| **ADR-008** (nueva) | Estructura del reemplazo | Hexagonal mínima: borde → aplicación → dominio puro → puertos → adaptadores | Un `app.py` monolítico con `if/elif`; Clean Architecture completa | El monolito oculta la precedencia y se rompe con el incidente; la Clean completa es ceremonia |
| **ADR-009** (nueva) | Precedencia de errores | Pipeline de etapas con orden declarado en el perfil; gana el primer error | `if` anidados; validación declarativa (Pydantic) | El orden es un comportamiento evaluado ("dos defectos por mensaje") y puede cambiar en el incidente |
| **ADR-010** (nueva) | Comandos | Registro `nombre → handler + aridad` (patrón Command) | Dispatcher con `if cmd == ...` | Un comando nuevo o cambiado es un archivo; la aridad queda declarada y comprobable |
| **ADR-011** (nueva) | Versionado del comportamiento | Perfiles `v1_manana` / `v2_incidente` heredables, elegidos por `BEHAVIOR_PROFILE`; goldens por perfil | Flags `if INCIDENT` sueltos; rama git por versión; perfiles 100 % YAML | El diff entre perfiles **es** la sección 6 de la spec; permite correr ambos en CI y revertir con una variable |
| **ADR-012** (nueva) | Errores | Catálogo como datos `{código: (status, cuerpo)}` + `DomainError(code)` | Strings de error en cada handler | Una sola fuente de verdad para los bytes exactos; la sección 5 de la spec se verifica contra él |
| ADR-004 (enmienda) | Hosting | Railway, `numReplicas: 1`, Serverless apagado, `railway.json`, healthcheck en `/health` aceptado solo con `Host: healthcheck.railway.app` | Healthcheck en `/healthz`; Serverless encendido; deploy sin healthcheck | Serverless devuelve 502 al despertar; una ruta extra rompe la paridad de E404; `/health` exige token, y la excepción por Host no la ve el jurado |
| **ADR-013** (nueva) | Red de seguridad | Diferencial + goldens por perfil en hook pre-push, smoke contra la URL tras cada deploy, logs JSON | Tests manuales; observabilidad completa (OTel/Prometheus) | Máximo de detección de regresiones con mínimo de montaje en 1 día |
| ADR-003 (enmienda) | Descubrimiento | Se agregan un generador por gramática con control válido y las "secuencias centinela" para el incidente | L\*/LearnLib; Pact; shadow traffic en vivo | L\* es overkill en 8 h; Pact no tiene consumidor; el reemplazo no puede llamar al original |

## Fuentes

- Fowler, *StranglerFigApplication*: https://martinfowler.com/bliki/StranglerFigApplication.html
- GitHub Scientist: https://github.com/github/scientist · Diffy: https://github.com/opendiffy/diffy · GoReplay: https://github.com/buger/goreplay
- ApprovalTests: https://approvaltests.com/ · Feathers, *Working Effectively with Legacy Code* (2004), cap. 13 "characterization tests"
- McKeeman, *Differential Testing for Software* (1998): https://www.cs.dartmouth.edu/~mckeeman/references/DifferentialTestingForSoftware.pdf
- Pact: https://docs.pact.io/
- Hypothesis stateful testing: https://hypothesis.readthedocs.io/en/latest/stateful.html
- Angluin, *Learning regular sets from queries and counterexamples* (1987): https://doi.org/10.1016/0890-5401(87)90052-6 · LearnLib: https://learnlib.de/
- The Fuzzing Book, *Grammars*: https://www.fuzzingbook.org/html/Grammars.html
- Cockburn, *Hexagonal Architecture*: https://alistair.cockburn.us/hexagonal-architecture/
- Chain of Responsibility: https://refactoring.guru/design-patterns/chain-of-responsibility
- FastAPI, errores y 422: https://fastapi.tiangolo.com/tutorial/handling-errors/
- Starlette routing: https://www.starlette.io/routing/
- Uvicorn server behavior: https://uvicorn.dev/server-behavior/
- Redis transactions: https://redis.io/docs/latest/develop/interact/transactions/
- Railway: App Sleeping https://docs.railway.com/reference/app-sleeping · Healthchecks https://docs.railway.com/guides/healthchecks · Scaling https://docs.railway.com/reference/scaling
