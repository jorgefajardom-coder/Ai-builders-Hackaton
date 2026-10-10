---
tags: [problema, reto2]
fuente: material/pruebas/ejemplos.jsonl
---
# Hallazgos iniciales (de los 20 ejemplos)

> [!warning] Todo aquí es **probable** hasta repetirlo contra el original y registrarlo en `experimentos.jsonl`. Los ejemplos se grabaron con la versión **de la mañana**: el servicio puede cambiar durante el día.

## Forma del mensaje
`POST /msg` con `{"m": "COMANDO;arg1;...;argN;CONTROL"}`. Separador `;`. El último campo es un **control numérico**.

## Comandos vistos
| Comando | Argumentos | Éxito | Ejemplo |
|---|---|---|---|
| `PING` | control | `200 {"pong":true}` | #1 |
| `ALTA` | nombre | `201 {"cuentaId":"AC-0001"}` (IDs secuenciales `AC-%04d`) | #3, #4 |
| `CONSULTA` | cuenta | `200 {"cuenta_id":…,"saldo":N}` ⚠️ usa `cuenta_id` (snake) y `ALTA` usa `cuentaId` (camel) | #5, #8 |
| `DEPOSITO` | cuenta, monto | `200 {"status":"recieved","operacionId":"OP-0001"}` ⚠️ typo `recieved` | #6, #18 |
| `TRANSFER` | origen, destino, monto | igual que `DEPOSITO`; los IDs `OP-%04d` son compartidos | #7, #10 |
| `ANULA` | operación | `200 {"ok":true,"anulada":"OP-0003"}`; la segunda vez `200 {"ok":false,"motivo":"ya anulada"}` | #13, #14 |

- El comando **no distingue mayúsculas**: `CONSULTa` funciona y el control es el mismo que con `CONSULTA` (#11 vs #5).
- **Saldo inicial 0.** Montos enteros.
- `TRANSFER` 100000 pasa y 120000 da `E506 límite excedido` → límite por operación entre 100000 y 119999 (¿≤ 100000?).
- Después de `ANULA OP-0003`, ¿se revierte el saldo? → **por probar** (ningún ejemplo consulta después).

## Errores vistos
| Código | Status | Mensaje (exacto) | Disparador | Ejemplo |
|---|---|---|---|---|
| E201 | 400 | `control mal formado` | control no numérico (`5X`) | #17 |
| E202 | 400 | `control inválido` | control numérico pero incorrecto | #2 |
| E301 | 400 | `comando desconocido ` ⚠️ **espacio final** | `SALDOS` | #12 |
| E302 | 400 | `aridad inválida` | `ALTA` con 2 args | #20 |
| E401 | 404 | `cuenta inexistente` | `CONSULTA AC-0009` | #15 |
| E506 | 422 | `límite excedido` | transfer de 120000 | #9 |
| E507 | 422 | `saldo insuficiente` | transfer > saldo | #16 |

Familias de códigos: **2xx = integridad · 3xx = sintaxis · 4xx = existencia · 5xx = reglas de negocio**. El orden de evaluación está por determinar.

## El control (pendiente)
Pares válidos conocidos: `ALTA;Lucia→82`, `ALTA;Mateo→3`, `CONSULTA;AC-0001→14`, `…0002→11`, `…0009→87`, `ANULA;OP-0003→66`, …
- Cambiar el último dígito de la cuenta de 1→2 baja el control en 3; 1→9 lo baja en 24 (14−24 = −10 ≡ **87 mod 97**). Sugiere **una combinación lineal mod 97**.
- Descartados con fuerza bruta: suma de bytes, hash polinomial `h·B+c` y sumas ponderadas por posición (i, n−i, 1/3 alternos), sobre el mensaje completo, en mayúsculas o solo con los argumentos (`scratch ck*.py`).
- **Siguiente paso:** experimentos controlados en vivo, variando **un carácter a la vez** y midiendo cuánto cambia el control → peso de cada posición.
- `PING;XX` responde `pong` según el README → ¿PING no valida el control?

## Inconsistencias a replicar (no corregir)
- `recieved` (typo)
- `cuentaId` vs `cuenta_id`
- espacio final en `"comando desconocido "`
- `ANULA` repetido devuelve **200** con `ok:false` (no un 4xx)
