# Especificación del servicio "caja negra"

> Documento para que otro ingeniero reimplemente el servicio **sin tocar el original**.
> Cada comportamiento: **ID · descripción · evidencia** (los `id` de [`experimentos.jsonl`](../experimentos.jsonl); "ejemplo N" = línea N de `material/pruebas/ejemplos.jsonl`) **· confianza**:
> **confirmado** = probado y se repite (≥ 2 veces o predicho sobre entrada no vista) · **probable** = visto una vez o inferido · **supuesto** = no probado; es lo que hace nuestro reemplazo por defecto.
>
> Versión descrita: la vigente durante la mañana del 2026-10-10. Los cambios del día van en §6.
> Implementación de referencia: [`app/`](../app) (reemplazo) y [`app/checkval.py`](../app/checkval.py) (control).

## 1. Entrada
_Rutas, métodos, autenticación, forma del cuerpo y límites._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| EN-01 | `GET /health` con token → `200 {"ok":true}` | 1 | probable |
| EN-02 | Sin token, token inválido o `bearer` en minúsculas → `401 {"error":"E001","mensaje":"no autorizado"}` en `/health`, `/msg`, `/__reset` | 2, 5–9, 1406, 1408, 1409 | confirmado |
| EN-03 | Ruta desconocida o método distinto (incluidos OPTIONS y HEAD; HEAD sin cuerpo) → `404 {"error":"E404","mensaje":"ruta desconocida"}`, **antes** de la auth y del tamaño (rutas sensibles a mayúsculas y a la barra final) | 10–18, 1410, 1579, 1580 | confirmado |
| EN-04 | `POST /__reset` → `200 {"ok":true}`; ignora el cuerpo (incluso de 9000 bytes) | 3, 19, 1411 | confirmado |
| EN-05 | Límite de cuerpo: **8192 bytes crudos**. 8192 → se procesa; ≥8193 → `413 {"error":"E101","mensaje":"cuerpo demasiado grande"}` (medido con relleno de espacios, no depende de `m`) | 1398, 1401, 1404, 1405, 1384 | confirmado |
| EN-06 | Orden de entrada: ruta → auth → tamaño → JSON (8193 bytes sin token → 401; 8193 bytes de JSON inválido → 413) | 1406, 1407, 1408 | probable |
| EN-07 | Cuerpo que no es JSON válido (texto, vacío, sin cuerpo, JSON + basura) → `400 {"error":"E100","mensaje":"json inválido"}` | 1366, 1367, 1368, 1381 | confirmado |
| EN-08 | JSON válido pero sin `m` string (objeto vacío, `M` mayúscula, `m` número/null/array, cuerpo array/string/null) → `400 {"error":"E102","mensaje":"falta m"}` | 1369–1373, 1375–1377 | confirmado |
| EN-09 | `m` = `""` pasa E102 y da `E103` | 1282 | probable |
| EN-10 | Claves extra se ignoran; el `Content-Type` de la petición no importa (text/plain o ausente se parsea igual) | 1374, 1378, 1379 | confirmado |
| EN-11 | Clave `m` duplicada: se acepta y **gana la última** (semántica de `JSON.parse`) | 1380, 1578 | probable |
| EN-12 | Todas las respuestas son JSON con `Content-Type: application/json; charset=utf-8` | todo el log | confirmado |
| EN-13 | Header `X-Req`: contador **por token** de peticiones autenticadas a `/msg` (incluye E100/E101/E102 y errores de negocio); no aparece en 401/404/`/__reset`/`/health`; **no** se reinicia con `/__reset`. Los headers no se comparan en la evaluación | 4, 37, 1249, 1366, 1384, 1406, 1410 | confirmado |

## 2. Integridad
_Cómo valida el servicio que un mensaje está bien formado._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| IN-01 | `m` = `CMD;arg1;…;argN;CONTROL`. Se parte por `;`. Si no hay ningún `;` → `400 {"error":"E103","mensaje":"falta control"}` | 1278, 1281, 1282, 1285 | confirmado |
| IN-02 | Si algún segmento (comando, argumento o control) es vacío → `400 {"error":"E104","mensaje":"segmento vacío"}`; se evalúa antes que el control y que PING. Un espacio `" "` NO es vacío | 1269, 1279, 1283, 1284, 1299–1302, 1304, 1305, 1386, 1349 | confirmado |
| IN-03 | **Fórmula del control** (ISO 7064 mod 97-10, estilo IBAN): cuerpo = todo antes del último `;` (comando incluido). N = concatenación decimal de cada carácter: dígito ASCII → él mismo; letra ASCII (sin distinguir mayúsculas) → su posición A=1…Z=26 en decimal (J…Z aportan dos cifras); cualquier otro carácter (`;`, `-`, espacio, `'`, `_`, acentos, ñ, CJK, emoji) no aporta nada. `control = 98 − (N·100 mod 97)` → rango 2…98 | ajuste 38/38 (`bench/fit_alfa.py`); predicciones 1249–1258 (10/10), 1286, 1306, 1312–1339, 1341–1364, 1413–1520 | confirmado |
| IN-04 | Letras sin distinguir mayúsculas en el control (`consulta;AC-0001` → 14, igual que `CONSULTA`) | 1252, 1258, ejemplo 11 | confirmado |
| IN-05 | Caracteres no ASCII se ignoran en el control (`José`, `ñandú`, `李小龙`, `😀`, `ÁLTA`) | 1339, 1342, 1346, 1347, 1348 | confirmado |
| IN-06 | Formato del control: exactamente **1 o 2 dígitos ASCII** (`^[0-9]{1,2}$`); si no → `400 {"error":"E201","mensaje":"control mal formado"}` (`014`, `0014`, `111`, `100`, `-83`, `+14`, `" 14"`, `"14 "`, `14.0`, `１４`, `0x0E`, `1e1`, `5X`, `XX`) | 1262–1268, 1270–1273, 1297, 1288, ejemplo 17 | confirmado |
| IN-07 | Con formato válido, el control debe ser **exactamente** el decimal canónico (sin cero a la izquierda): `08` para 8 → E202; `0`, `00`, `99` → E202. Error: `400 {"error":"E202","mensaje":"control inválido"}` | 1292, 1293, 1294–1296, 1259, 1260, ejemplo 2 | confirmado |
| IN-08 | `PING` (comando sin distinguir mayúsculas) **no valida el control**: `PING;XX`, `PING;63`, `Ping;XX` → pong. Sí aplican E103, E104 y aridad (E302) | 1274, 1275, 1277, 1574, 1278, 1279, 1280, 1303 | confirmado |
| IN-09 | Los comandos desconocidos **sí** validan el control: E201/E202 antes que E301 | 1287, 1288, 1309 | confirmado |
| IN-10 | El control se valida antes que la aridad (E202 antes que E302) | 405, 1289 | confirmado |

Implementación de referencia: `bench/control_model.py` (`control(body)`, `is_valid(msg)`).

```python
def control(body):
    r = 0
    for ch in body:
        if '0' <= ch <= '9': ds = ch
        elif ch.isascii() and ch.isalpha(): ds = str(ord(ch.upper()) - 64)
        else: continue
        for d in ds: r = (r * 10 + int(d)) % 97
    return 98 - (r * 100) % 97
```

## 3. Comandos
_Un bloque por comando: argumentos, efecto y respuesta._

Nombre de comando: sin distinguir mayúsculas, **sin recortar espacios** (`"CONSULTA "`, `" PING"`, `"\tPING"` → E301). Los argumentos tampoco se recortan.

### PING
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CP-01 | `PING;<cualquier cosa no vacía>` → `200 {"pong":true}` sin validar el control | 4, 1274–1277, 1374, 1574 | confirmado |
| CP-02 | `PING;X;<ctrl>` (dos segmentos tras el comando) → `400 E302` aunque el control sea `XX` | 1280, 1303 | confirmado |

### ALTA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CA-01 | `ALTA;<nombre>;<ctrl>` → `201 {"cuentaId":"AC-0001"}`; ids secuenciales `AC-%04d` desde 0001 tras cada reset | 1249–1251, 1341–1354, ejemplos 3–4 | confirmado |
| CA-02 | Cualquier nombre no vacío se acepta: espacios, solo espacio, acentos, ñ, CJK, emoji, apóstrofo, dígitos, solo dígitos, 60/300/5000/8176 letras | 1341–1354, 1383, 1398 | confirmado |
| CA-03 | Nombres duplicados (también en otra capitalización) crean cuentas nuevas | 1350–1352 | confirmado |
| CA-04 | Aridad: 0 o ≥2 argumentos → `400 E302` | 1567, ejemplo 20 | confirmado |
| CA-05 | El nombre no se devuelve en ninguna respuesta | todo el log | probable |
| CA-06 | Formato de id a partir de AC-9999 (¿`AC-10000`?) | — | supuesto |

### CONSULTA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CC-01 | `CONSULTA;<cuenta>` → `200 {"cuenta_id":"AC-0001","saldo":N}` (clave en snake_case; saldo entero, puede ser negativo) | 1252, 1355, 1504, 1572, ejemplos 5, 8 | confirmado |
| CC-02 | Coincidencia **exacta** del id: `ac-0001`, `" AC-0001"`, `"AC-0001 "`, `AC-1`, `AC-00001`, `AC0001`, `AC--0001`, `XX-0001`, `OP-0001` → `404 {"error":"E401","mensaje":"cuenta inexistente"}` (no hay error de formato de cuenta) | 1356–1364 | confirmado |
| CC-03 | Aridad distinta de 1 → E302 | 1290, 1568, 405 | confirmado |

### DEPOSITO
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CD-01 | `DEPOSITO;<cuenta>;<monto>` → `200 {"status":"recieved","operacionId":"OP-0001"}` (typo `recieved`); suma el monto al saldo | 1253, 1420, 1421, 1426, ejemplos 6, 18 | confirmado |
| CD-02 | Monto válido = `^[1-9][0-9]{0,9}$` (1 … 9 999 999 999). `0`, `-5`, `10.5`, `abc`, `007`, `1e3`, `" 100"`, `+100`, 11+ dígitos → `400 {"error":"E303","mensaje":"monto inválido"}` | 1414–1418, 1422–1425, 1432–1472 | confirmado |
| CD-03 | Sin límite de negocio en el depósito (100001 y 1 000 000 aceptados) | 1420, 1421 | confirmado |
| CD-04 | E303 se evalúa antes que la existencia de la cuenta (E401) | 1427, 1428 | confirmado |
| CD-05 | Aridad distinta de 2 → E302 (antes que E303) | 1429, 1566 | confirmado |

### TRANSFER
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CT-01 | `TRANSFER;<origen>;<destino>;<monto>` → `200 {"status":"recieved","operacionId":…}`; resta del origen y suma al destino | 1477, 1479, 1481, 1489, 1492, ejemplos 7, 10 | confirmado |
| CT-02 | Límite **por operación** ≤ 100000 (inclusivo); 100001 → `422 {"error":"E506","mensaje":"límite excedido"}`; no es acumulado (dos de 100000 seguidas pasan) | 1477, 1478, 1479, 1487, 1488, ejemplo 9 | confirmado |
| CT-03 | Origen = destino → `400 {"error":"E304","mensaje":"origen y destino iguales"}` (aunque la cuenta no exista o el monto supere el límite) | 1480, 1490, 1491, 1514, 1516 | confirmado |
| CT-04 | Saldo insuficiente → `422 {"error":"E507","mensaje":"saldo insuficiente"}`; transferir exactamente el saldo está permitido | 1573, 1570, ejemplo 16 | confirmado |
| CT-05 | Orden: E302 → E303 → E304 → E401 (origen o destino) → E506 → E507 | 1493, 1485, 1515, 1514, 1486, 1520, 1519 | confirmado |
| CT-06 | Mismo formato de monto que DEPOSITO (E303) | 1482, 1485 | probable |

### ANULA
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CN-01 | `ANULA;<op>` → `200 {"ok":true,"anulada":"OP-0002"}` | 1255, 1498, 1503, 1512, 1571, ejemplo 13 | confirmado |
| CN-02 | Revierte el efecto: un depósito anulado resta el monto; una transferencia anulada devuelve el monto al origen y lo quita al destino | 1499, 1504, 1505, 1513, 1256 | confirmado |
| CN-03 | **No comprueba saldo**: puede dejar saldos negativos (−500, −300) | 1504, 1572 | confirmado |
| CN-04 | Anular una operación ya anulada → `200 {"ok":false,"motivo":"ya anulada"}` | 1506, ejemplo 14 | confirmado |
| CN-05 | Id inexistente, en minúsculas, sin relleno o de cuenta → `404 {"error":"E402","mensaje":"operación inexistente"}` | 741, 1507–1510 | confirmado |
| CN-06 | ANULA no consume número de operación | 1500 | probable |
| CN-07 | Aridad distinta de 1 → E302 | 1511 | probable |

## 4. Memoria entre requests
_Qué recuerda el servicio y qué cambia una respuesta según los requests anteriores._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| ME-01 | Estado por token: cuentas (contador AC), saldos, operaciones (contador OP compartido entre DEPOSITO y TRANSFER) y operaciones anuladas | 1253–1255, 1497–1513 | confirmado |
| ME-02 | Las operaciones fallidas (E303/E506/E507/…) no consumen número de OP ni modifican saldos | 1478→1479, 1414–1419 | confirmado |
| ME-03 | `/__reset` deja todo vacío: contadores AC y OP vuelven a 0001, saldos y anulaciones se borran | 1249, 1341, 1413, 1474, 1495 | confirmado |
| ME-04 | Determinista: los 20 ejemplos repetidos dos veces tras reset dan respuestas idénticas a las grabadas | 1521–1562 | confirmado |
| ME-05 | La validez del control depende solo del texto, no del estado | ejemplos 5 y 11, 1252, 1355 | confirmado |

## 5. Errores
_Cada error con su status, su cuerpo exacto y en qué orden se evalúa frente a los otros._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| ER-01 | Todos los errores son JSON `{"error":"<código>","mensaje":"<texto>"}` con `Content-Type: application/json; charset=utf-8`; gana el **primer** error según el orden ER-02 | todo el log | confirmado |
| ER-02 | **Orden de evaluación:** ruta/método (E404) → auth (E001) → tamaño (E101) → JSON (E100) → `m` string (E102) → hay `;` (E103) → segmento vacío (E104) → si es PING: aridad (E302) o pong sin control → formato de control (E201) → valor de control (E202) → comando (E301) → aridad (E302) → monto (E303) → origen=destino (E304) → existencia (E401/E402) → límite (E506) → saldo (E507) | 12, 1410, 1406, 1407, 1408, 1366, 1282, 1301, 1302, 1305, 1303, 1288, 1287, 1289, 1306, 1566, 1427, 1485, 1514, 1516, 1486, 1520, 1519, 1573 | confirmado |
| ER-03 | E404 · 404 · `{"error":"E404","mensaje":"ruta desconocida"}` — ruta o método inexistente (también OPTIONS; HEAD sin cuerpo), sin importar el token | 10–18, 1410, 1579, 1580 | confirmado |
| ER-04 | E001 · 401 · `{"error":"E001","mensaje":"no autorizado"}` — sin token, token ajeno o esquema `bearer` en minúsculas | 2, 5–9, 1406 | confirmado |
| ER-05 | E101 · 413 · `{"error":"E101","mensaje":"cuerpo demasiado grande"}` — cuerpo de más de 8192 bytes | 1384, 1405 | confirmado |
| ER-06 | E100 · 400 · `{"error":"E100","mensaje":"json inválido"}` | 1366–1368, 1381 | confirmado |
| ER-07 | E102 · 400 · `{"error":"E102","mensaje":"falta m"}` | 1369–1377 | confirmado |
| ER-08 | E103 · 400 · `{"error":"E103","mensaje":"falta control"}` — `m` sin ningún `;` (incluido `""`) | 1278, 1281, 1282 | confirmado |
| ER-09 | E104 · 400 · `{"error":"E104","mensaje":"segmento vacío"}` | 1269, 1299 | confirmado |
| ER-10 | E201 · 400 · `{"error":"E201","mensaje":"control mal formado"}` — control que no es `^[0-9]{1,2}$` | 1262–1273 | confirmado |
| ER-11 | E202 · 400 · `{"error":"E202","mensaje":"control inválido"}` — control con formato válido pero distinto del canónico | 1259, 1260, 1292 | confirmado |
| ER-12 | E301 · 400 · `{"error":"E301","mensaje":"comando desconocido "}` (**espacio final**). Si el comando en mayúsculas está a distancia de Levenshtein ≤ 2 de uno conocido, agrega `"sugerencia":"<CMD>"`; en empate gana el primero alfabético (ALTA) | 1286, 1306, 1312–1339, 1576 | confirmado |
| ER-13 | E302 · 400 · `{"error":"E302","mensaje":"aridad inválida"}` | 1290, 1567 | confirmado |
| ER-14 | E303 · 400 · `{"error":"E303","mensaje":"monto inválido"}` — monto que no es `^[1-9][0-9]{0,9}$` | 1414–1418 | confirmado |
| ER-15 | E304 · 400 · `{"error":"E304","mensaje":"origen y destino iguales"}` | 1480, 1490 | confirmado |
| ER-16 | E401 · 404 · `{"error":"E401","mensaje":"cuenta inexistente"}` | 1356–1364 | confirmado |
| ER-17 | E402 · 404 · `{"error":"E402","mensaje":"operación inexistente"}` | 1507–1510 | confirmado |
| ER-18 | E506 · 422 · `{"error":"E506","mensaje":"límite excedido"}` — TRANSFER de más de 100000 | 1478, 1519 | confirmado |
| ER-19 | E507 · 422 · `{"error":"E507","mensaje":"saldo insuficiente"}` | 1573 | confirmado |
| ER-20 | ANULA de una operación ya anulada **no es error**: `200 {"ok":false,"motivo":"ya anulada"}` | 1506, ejemplo 14 | confirmado |
| ER-21 | Excepción interna inesperada: el reemplazo responde `500 {"error":"E500","mensaje":"error interno"}` (nunca observado en el original) | — | supuesto |

### Supuestos del reemplazo (lo no observado; ADR-006)
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| SU-01 | Ids a partir de AC-9999 / OP-9999: se siguen numerando sin truncar (`AC-10000`) | — | supuesto |
| SU-02 | Saldos sin tope (enteros de precisión arbitraria); el original podría perder precisión por encima de 2^53 | — | supuesto |
| SU-03 | `/health` sin token responde `200 {"ok":true}` solo si `Host: healthcheck.railway.app` (healthcheck del despliegue; el jurado nunca usa ese Host) | ADR-004 | supuesto |

## 6. Cambios durante el día
_Qué cambió, desde cuándo y cómo lo detectamos._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CB-01 | Hasta el log 1562 el servicio responde igual que los ejemplos de la mañana (sin cambios detectados) | 1521–1562 | confirmado |
| CB-02 | Para detectar el cambio: volver a correr `bench/exp18_determinismo.py` y `bench/exp05_formula.py` tras las 15:30 | — | supuesto |
| CB-03 | Detección continua: `bench/sentinel.py` corre un set fijo de secuencias contra el original cada 10 min y compara cada respuesta con el reemplazo (perfil v1); cualquier diferencia queda en el log (seq `centinela-*`) y en `docs/04 Ejecución/Centinela.md` | seq `centinela-*` | confirmado |

## 7. Riesgos
_Comportamientos que un cliente nuevo no debería heredar y cómo los cerraríamos._

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| RI-01 | ANULA deja saldos negativos sin comprobar fondos: un cliente nuevo no debería heredarlo → validar saldo o anular solo si el destino conserva el monto | 1504, 1572 | confirmado |
| RI-02 | El control mod 97 no es autenticación (se calcula sin secreto) y PING ni siquiera lo valida → usar firma HMAC con clave por cliente | 1274, 1275, IN-03 | confirmado |
| RI-03 | La sugerencia de E301 filtra la lista de comandos a quien tantea | 1312–1339 | confirmado |
| RI-04 | Sin validación de nombre (emoji, 8 KB, duplicados) → normalizar y limitar longitud | 1347–1354, 1398 | confirmado |
| RI-05 | Ids secuenciales predecibles y E401 vs 200 permiten enumerar cuentas → ids opacos | 1355–1364 | confirmado |
| RI-06 | `X-Req` expone el volumen de tráfico del token | EN-13 | confirmado |
| RI-07 | La ruta se evalúa antes que la auth (404 vs 401 revela qué rutas existen) | 12, 1410 | confirmado |
| RI-08 | Inconsistencias a replicar pero no heredar: `recieved`, `cuentaId` vs `cuenta_id`, espacio final en `comando desconocido `, ANULA repetida con 200 | ejemplos 6, 3, 5, 12, 14 | confirmado |
| RI-09 | Montos de hasta 10 dígitos sin límite de depósito; saldos sin tope → posible desbordamiento por encima de 2^53 | 1421, 1435 | probable |
