"""Exp 16 — TRANSFER: frontera del límite, límite acumulado, misma cuenta, precedencia E303/E401/E506/E507."""
from control_model import control
from prober import msg, reset, show

S = "s16-transfer"
reset(S, "estado limpio: reglas de TRANSFER")


def m(body, h):
    e = msg(f"{body};{control(body)}", S, h)
    show(e)
    return e


m("ALTA;Ana", "crear AC-0001 (origen)")
m("ALTA;Beto", "crear AC-0002 (destino)")
m("DEPOSITO;AC-0001;500000", "fondear AC-0001 con 500000 -> OP-0001")
CASOS = [
    ("TRANSFER;AC-0001;AC-0002;100000", "exactamente 100000: límite inclusivo -> 200 OP-0002"),
    ("TRANSFER;AC-0001;AC-0002;100001", "100001: si el límite es <=100000 -> 422 E506"),
    ("TRANSFER;AC-0001;AC-0002;100000", "segunda de 100000: si el límite es por operación -> 200; si es acumulado -> E506"),
    ("TRANSFER;AC-0001;AC-0001;10", "transferencia a la misma cuenta: ¿error propio o 200?"),
    ("CONSULTA;AC-0001", "saldo de AC-0001 (500000 - 200000 = 300000 si las anteriores se aplicaron y la de misma cuenta es neutra)"),
    ("TRANSFER;AC-0001;AC-0002;0", "monto 0 -> E303"),
    ("TRANSFER;AC-0001;AC-0009;10", "destino inexistente -> E401"),
    ("TRANSFER;AC-0009;AC-0002;10", "origen inexistente -> E401"),
    ("TRANSFER;AC-0009;AC-0002;abc", "origen inexistente + monto inválido: E303 antes que E401 (como en DEPOSITO)"),
    ("TRANSFER;AC-0009;AC-0002;200000", "origen inexistente + sobre el límite: ¿E401 o E506 primero?"),
    ("TRANSFER;AC-0002;AC-0001;200000", "sobre el límite + saldo insuficiente (AC-0002 tiene 200000? o menos): ¿E506 o E507 primero?"),
    ("TRANSFER;AC-0002;AC-0001;150000", "sobre el límite con saldo suficiente si AC-0002 tiene 200000 -> E506"),
    ("CONSULTA;AC-0002", "saldo de AC-0002"),
    ("TRANSFER;AC-0001;AC-0001;200000", "misma cuenta + sobre el límite: ¿E506 o error de misma cuenta?"),
    ("TRANSFER;AC-0002;AC-0002;99999", "misma cuenta + saldo suficiente: ¿200?"),
    ("TRANSFER;AC-0002;AC-0001;1", "1 unidad: mínimo válido -> 200"),
    ("TRANSFER;AC-0001;AC-0002", "TRANSFER con 2 argumentos -> E302"),
]
for b, h in CASOS:
    m(b, h)
