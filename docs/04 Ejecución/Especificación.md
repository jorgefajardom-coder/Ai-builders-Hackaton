---
tags: [ejecucion, reto2, entregable]
entrega: "20:00"
---
# Especificación del servicio original

> [!important] Formato obligatorio (README del material)
> - Cada comportamiento tiene **ID · Comportamiento · Evidencia · Confianza**.
> - **Evidencia** = los `id` de las líneas de `experimentos.jsonl` que lo prueban.
> - **Confianza:** `confirmado` (probado y se repite) · `probable` (visto una vez o inferido) · `supuesto` (no probado; es lo que hace el reemplazo por defecto).
> - El juez puntúa cada comportamiento bien descrito con evidencia. **Una afirmación falsa resta** → ante la duda, `probable` o `supuesto`, nunca `confirmado`.
>
> Versión entregable final: `spec/ESPECIFICACION.md` en el repo. Esta nota es el borrador de trabajo.

## 1. Entrada
_Rutas, métodos, autenticación, forma del cuerpo y límites._
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| IN-01 | | | |

## 2. Integridad
_Cómo valida el servicio que un mensaje está bien formado (control)._
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| INT-01 | | | |

## 3. Comandos
_Un bloque por comando: argumentos, efecto y respuesta._
### PING
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
### ALTA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
### CONSULTA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
### DEPOSITO
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
### TRANSFER
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
### ANULA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 4. Memoria entre requests
_Qué recuerda el servicio y qué cambia una respuesta según los requests anteriores._
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| MEM-01 | | | |

## 5. Errores
_Cada error con su status, su cuerpo exacto y el orden en que se evalúa frente a los demás._
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| ERR-01 | | | |

## 6. Cambios durante el día
_Qué cambió, desde cuándo y cómo lo detectamos._ → [[Incidente]]
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 7. Riesgos
_Comportamientos que un cliente nuevo no debería heredar y cómo los cerraríamos._
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| RSK-01 | | | |
