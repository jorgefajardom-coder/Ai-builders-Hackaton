"""Exp 15 — Monto máximo aceptado por DEPOSITO (20 dígitos -> E303 en log 1422; 1000000 ok en 1421).
Primero sondeo por número de dígitos (9..19), luego bisección del valor en la primera longitud rechazada."""
from control_model import control
from prober import msg, reset, show

S = "s15-monto-max"
reset(S, "estado limpio: monto máximo de DEPOSITO")


def m(body, h):
    e = msg(f"{body};{control(body)}", S, h)
    show(e)
    return e


m("ALTA;Ana", "crear AC-0001")
ok_len = None
for d in range(7, 20):
    e = m(f"DEPOSITO;AC-0002;{'9' * d}", f"monto de {d} nueves a cuenta inexistente: si el formato del monto acepta {d} dígitos -> E401, si no -> E303")
    if e["response"].get("error") == "E303":
        break
    ok_len = d
print("máximo de dígitos aceptado:", ok_len)
lo, hi = int("9" * ok_len), int("9" * (ok_len + 1))
while hi - lo > 1:
    mid = (lo + hi) // 2
    e = m(f"DEPOSITO;AC-0002;{mid}", f"bisección del monto máximo: {lo} pasa formato (E401) y {hi} no (E303); ¿{mid}?")
    if e["response"].get("error") == "E303":
        hi = mid
    else:
        lo = mid
print("monto máximo:", lo, "primer rechazado:", hi)
