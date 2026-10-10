---
tags: [ejecucion, incidente]
---
# Incidente: versión 2 del original

> [!warning] Llegó a mitad del día y sin aviso. Fuente de verdad del comportamiento: `spec/ESPECIFICACION.md` §6 (CB-04…CB-10). Esta nota cuenta cómo respondimos.

## Qué cambió
- **Hora:** entre las ~15:30 y las 15:55 (la última vuelta del centinela en v1 es el log 3164; la regresión que ya ve v2 empieza en el 3165).
- **Descripción (tal como llegó):** "Cambiaron 3 comportamientos, el resto es idéntico a v1. Encuentren los 3 cambios, regístrenlos en el log de experimentos y hagan que el reemplazo se comporte como v2. Los tests de conformidad corren contra v2."
- **Los 3 cambios:**

| ID | Qué | v1 | v2 | Evidencia |
|---|---|---|---|---|
| CB-04 | Saldo en `CONSULTA` | entero: `"saldo":110000` | string, centavos ÷ 100 con 2 decimales: `"saldo":"1100.00"`, `"0.05"`, `"-3.00"` (sin separador de miles) | 3504, 3547, 3698–3721 |
| CB-05 | Límite por `TRANSFER` | ≤ 100000 | **≤ 50000** (inclusivo; mismo E506, mismo orden, sigue contando para el antifraude) | 3452, 3506, 3740–3761 |
| CB-06 | `E510` cuenta bloqueada | `409 {"error","mensaje"}` | `423` + `"intentos": N` (E510 de esa cuenta desde su bloqueo: 1, 2, 3…; por cuenta; vuelve a 1 tras desbloquear y re-bloquear) | 3580, 3581, 3771–3805 |

Lo que **no** cambió (verificado): la entrada de montos (enteros, `10.50` → E303), DEPOSITO sin límite, umbral y desbloqueo del antifraude, precedencia de errores, fórmula del control, PING, NOTAS, HALT;x, rutas y auth (regresión 451/491 iguales; las 40 distintas se explican por los 3 cambios; exp29 20/20; barrido de 191 requests de un paso 0 diferencias).

## Impacto
- **Qué componentes afecta:** solo `CONSULTA` (formato de salida), `TRANSFER` (límite y E510) y el catálogo de errores (E510). Pipeline, control, rutas y auth intactos → [[Arquitectura]]
- **Qué supuestos rompe:** "el saldo es un entero" y "el límite es 100000"; además el estado por cuenta suma un contador (`intentos`) → [[Supuestos y alcance]]
- **Evals antes del cambio:** paridad local 100 % contra v1 (154 casos); set oficial 87/100 (14:45).
- **Evals después del cambio (sin arreglar):** perfil v1 contra los casos grabados en v2: 25/47 casos (53,2 %), 87,6 % de pasos. Set oficial 87/100 también a las 16:05 (el set ya espera v2: fallan 13 tests, 9 por status y 4 por cuerpo, coherente con E506/E510 por status y saldo por cuerpo).

## Respuesta
| Hora | Acción | Resultado |
|---|---|---|
| ~15:55 | Regresión completa del corpus de la mañana contra el original (`bench/regresion.py`, seq `v2-*`, log 3165–3694) | 40 respuestas distintas de 491 → 3 patrones (`bench/regresion_v2.json`) |
| 16:00 | Clasificación de las 40 diferencias | 16 formato de saldo, 4 E506 en 100000, 9 E510; 11 consecuencias del nuevo límite (saldos, ANULA → E402, OP corridos, un E507) |
| 16:02 | exp26: formato del saldo | 2 decimales siempre, sin miles, signo `-`, entrada sin cambios |
| 16:04 | exp27: búsqueda del límite (50000/50001 primero, luego binaria) | L = 50000 inclusivo, por operación, E506 antes de E507, cuenta para el bloqueo |
| 16:06 | exp28: `intentos` | contador por cuenta de E510 desde el bloqueo; validaciones y otros comandos no lo mueven; se reinicia al desbloquear |
| 16:08 | exp29–30: sanidad del resto + barrido de un paso (pedido tras ver 1 test que falla en su primer request) | 20/20 predicciones; 191 requests sin estado: 0 diferencias contra el perfil v2 |
| 16:10 | Perfil `v2` en el reemplazo (hereda de v1; 3 parámetros + 1 entrada del catálogo); `v2` por defecto | `diff.py` 100 % en ambas eras |
| 16:12 | `diff.py` por era (`CORTE_V2 = 3164`, `--profile`), centinela contra v2 | v1: 154/154 · v2: 48/48 casos |

## Decisiones tomadas
- **ADR-011 aplicado tal cual:** `v2 = replace(V1, …)` con `limite_transfer=50000`, `formato_saldo="decimal2"`, `e510_intentos=True` y `E510 → 423`. Los comandos leen esos parámetros del perfil que reciben; no hay `if INCIDENT`. Rollback = `BEHAVIOR_PROFILE=v1`. → [[Decisiones]]
- **v2 por defecto** (`app/config.py`): el set oficial corre contra v2.
- El saldo de v2 se formatea con aritmética entera (`divmod`), no con flotantes, para que `"200001235.54"` salga exacto.

## Evals después del arreglo
| Métrica | Antes (v1 vs v1) | Durante (perfil v1 vs original v2) | Después (perfil v2) |
|---|---|---|---|
| Casos grabados en v1 (log ≤ 3164) | 154/154 | — | 154/154 con perfil v1 |
| Casos grabados en v2 (log > 3164) | — | 25/47 (53,2 %) | **48/48 (100 %)** |
| Set oficial (100 tests) | 87/100 | 87/100 | pendiente de deploy |

## Lecciones
- Un centinela solo ve lo que cubre y cuando corre: el nuestro estaba en verde porque no dio vueltas durante la ventana del cambio. La **regresión completa del corpus** fue lo que lo encontró; correrla justo después de un aviso es barato (~530 requests).
- Separar **cambios** de **consecuencias**: 40 diferencias se reducían a 3 causas; el límite nuevo arrastraba saldos, ANULA y numeración.
- Tener el perfil como dato (ADR-011) hizo el arreglo de 3 parámetros; las dos versiones conviven y se prueban por era.
- Las herramientas de prueba tienen que saber de versiones: sin `CORTE_V2`, el log mezclaba dos verdades.
