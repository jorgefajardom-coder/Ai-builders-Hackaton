"""Exp 13 — ¿El límite E101 es sobre los bytes crudos del cuerpo (8192) o sobre 'm'? y precedencia
entre tamaño, auth, JSON inválido y ruta. Exp 12: cuerpo de 8192 bytes ok (log 1398), 8194 -> 413 (1401)."""
from prober import call, reset, show

S = "s13-limite-entrada"
reset(S, "estado limpio: límite de bytes y precedencia de entrada")
J = {"Content-Type": "application/json"}
base = '{"m":"PING;64"}'  # 15 bytes


def pad(total, b=base):
    return b + " " * (total - len(b.encode()))


CASOS = [
    (dict(raw=pad(8192), headers=J), "cuerpo de 8192 bytes con 'm' corto (relleno de espacios): si el límite es de bytes -> pong"),
    (dict(raw=pad(8193), headers=J), "cuerpo de 8193 bytes con 'm' corto: si el límite es >8192 bytes crudos -> 413 E101"),
    (dict(raw=pad(8193), headers=J, auth="ninguno"), "8193 bytes sin token: ¿401 (auth primero) o 413 (tamaño primero)?"),
    (dict(raw=pad(8193, "no json"), headers=J), "8193 bytes de JSON inválido: ¿413 o E100?"),
    (dict(raw="no json", headers=J, auth="ninguno"), "JSON inválido sin token: ¿401 o E100? (auth vs parseo)"),
    (dict(body={}, auth="invalido"), "sin 'm' con token inválido -> esperamos 401"),
]
for kw, h in CASOS:
    show(call("POST", "/msg", seq=S, hipotesis=h, **kw))
show(call("POST", "/nada", seq=S, raw=pad(9000), headers=J, hipotesis="ruta inexistente con cuerpo grande: ¿404 (ruta primero) o 413?"))
show(call("POST", "/__reset", seq=S, raw=pad(9000), headers=J, hipotesis="__reset con cuerpo de 9000 bytes: ¿ignora el cuerpo (200) o 413?"))
