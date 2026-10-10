"""Exp 14 — DEPOSITO: formato y límites del monto, precedencia con cuenta inexistente."""
from control_model import control
from prober import msg, reset, show

S = "s14-deposito"
reset(S, "estado limpio: validación de montos en DEPOSITO")


def m(body, h):
    e = msg(f"{body};{control(body)}", S, h)
    show(e)
    return e


m("ALTA;Ana", "crear AC-0001 para depósitos")
CASOS = [
    ("DEPOSITO;AC-0001;0", "monto 0: ¿error de monto (E5xx/E3xx) o 200?"),
    ("DEPOSITO;AC-0001;-5", "monto negativo (el '-' no cuenta en el control): ¿error de monto?"),
    ("DEPOSITO;AC-0001;10.5", "monto decimal: ¿error de formato?"),
    ("DEPOSITO;AC-0001;abc", "monto no numérico: ¿error de formato E3xx?"),
    ("DEPOSITO;AC-0001;007", "monto con ceros a la izquierda: ¿se acepta como 7?"),
    ("CONSULTA;AC-0001", "saldo tras los anteriores: revela cuáles se aplicaron"),
    ("DEPOSITO;AC-0001;100001", "100001 > límite de TRANSFER (100000): ¿DEPOSITO tiene límite?"),
    ("DEPOSITO;AC-0001;1000000", "un millón: ¿límite?"),
    ("DEPOSITO;AC-0001;99999999999999999999", "monto de 20 dígitos: ¿desbordamiento / límite?"),
    ("DEPOSITO;AC-0001;1e3", "notación científica"),
    ("DEPOSITO;AC-0001; 100", "espacio antes del monto"),
    ("DEPOSITO;AC-0001;+100", "signo + explícito"),
    ("CONSULTA;AC-0001", "saldo tras los grandes: revela cuáles se aplicaron y si hay pérdida de precisión"),
    ("DEPOSITO;AC-0009;0", "cuenta inexistente + monto 0: precedencia E401 vs error de monto"),
    ("DEPOSITO;AC-0009;abc", "cuenta inexistente + monto no numérico: precedencia"),
    ("DEPOSITO;AC-0001", "DEPOSITO sin monto -> E302"),
]
for b, h in CASOS:
    m(b, h)
