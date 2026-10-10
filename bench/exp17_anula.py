"""Exp 17 — ANULA: efecto en saldos, numeración de operaciones, saldos negativos, formatos de id;
más precedencias pendientes de TRANSFER (E304 vs E303/E401, E506 vs E507)."""
from control_model import control
from prober import msg, reset, show

S = "s17-anula"
reset(S, "estado limpio: efectos de ANULA")


def m(body, h):
    e = msg(f"{body};{control(body)}", S, h)
    show(e)
    return e


PASOS = [
    ("ALTA;Ana", "crear AC-0001"),
    ("ALTA;Beto", "crear AC-0002"),
    ("DEPOSITO;AC-0001;1000", "depósito -> OP-0001"),
    ("ANULA;OP-0001", "anular el depósito -> ok:true"),
    ("CONSULTA;AC-0001", "si ANULA revierte el depósito, saldo 0; si no, 1000"),
    ("DEPOSITO;AC-0001;1000", "nuevo depósito: si ANULA no consume número -> OP-0002"),
    ("TRANSFER;AC-0001;AC-0002;600", "transferencia 600 de 1 a 2 -> OP-0003"),
    ("TRANSFER;AC-0002;AC-0001;500", "AC-0002 gasta 500 de los 600 recibidos -> OP-0004 (AC-0002 queda en 100)"),
    ("ANULA;OP-0003", "anular la transferencia de 600 cuando el destino solo tiene 100: ¿ok con saldo negativo, o error (E507 / ok:false)?"),
    ("CONSULTA;AC-0002", "saldo de AC-0002 tras anular OP-0003 (100 si no se revirtió; -500 si se revirtió sin chequeo)"),
    ("CONSULTA;AC-0001", "saldo de AC-0001 tras anular OP-0003"),
    ("ANULA;OP-0001", "anular de nuevo una ya anulada -> 200 ok:false 'ya anulada' (repite ejemplo 14)"),
    ("ANULA;OP-0099", "operación inexistente -> 404 E402"),
    ("ANULA;op-0002", "id de operación en minúsculas: ¿E402 (comparación exacta)?"),
    ("ANULA;OP-2", "id sin relleno: ¿E402?"),
    ("ANULA;AC-0001", "id de cuenta en lugar de operación: E402"),
    ("ANULA;OP-0002;X", "ANULA con 2 argumentos -> E302"),
    ("ANULA;OP-0004", "anular la transferencia de 500 (2->1) -> ok; revierte saldos"),
    ("CONSULTA;AC-0002", "saldo de AC-0002 tras anular OP-0004"),
    ("TRANSFER;AC-0009;AC-0009;10", "misma cuenta inexistente: ¿E304 o E401 primero?"),
    ("TRANSFER;AC-0001;AC-0001;abc", "misma cuenta + monto inválido: ¿E303 o E304 primero?"),
    ("TRANSFER;AC-0001;AC-0001;200000", "misma cuenta + sobre el límite -> E304 (repite 1490)"),
    ("DEPOSITO;AC-0002;5", "dejar AC-0002 con saldo pequeño"),
    ("CONSULTA;AC-0002", "saldo de AC-0002 antes de la prueba E506/E507"),
    ("TRANSFER;AC-0002;AC-0001;200000", "saldo insuficiente + sobre el límite: ¿E506 o E507 primero?"),
    ("TRANSFER;AC-0001;AC-0009;200000", "origen existente, destino inexistente, sobre el límite: ¿E401 o E506?"),
]
for b, h in PASOS:
    m(b, h)
