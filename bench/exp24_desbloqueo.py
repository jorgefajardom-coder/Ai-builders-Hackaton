"""Exp 24 — ¿Un DEPOSITO exitoso desbloquea una cuenta bloqueada por antifraude? (afirmado en fix/two-fixes).

Se bloquea AC-0001 con 3 E507, se deposita y se reintenta transferir desde ella.
Controles: bloqueo sin depósito (debe seguir E510) y depósito fallido (E303) que no debería desbloquear.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


def bloquear(seq):
    reset(seq)
    m("ALTA;Ana", seq, "AC-0001")
    m("ALTA;Beto", seq, "AC-0002")
    m("DEPOSITO;AC-0001;1000", seq, "saldo 1000")
    for i in range(1, 4):
        m("TRANSFER;AC-0001;AC-0002;5000", seq, f"E507 #{i} para bloquear AC-0001")
    m("TRANSFER;AC-0001;AC-0002;100", seq, "confirmar bloqueo → E510")


S = "s24a-deposito-desbloquea"
bloquear(S)
m("DEPOSITO;AC-0001;10", S, "depósito exitoso a la cuenta bloqueada")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras el depósito: ¿desbloqueada (200) o sigue E510?")
m("TRANSFER;AC-0001;AC-0002;5000", S, "si se desbloqueó: ¿el contador de fallos volvió a 0? (E507 #1)")
m("TRANSFER;AC-0001;AC-0002;5000", S, "E507 #2")
m("TRANSFER;AC-0001;AC-0002;100", S, "con 2 fallos tras desbloqueo: ¿pasa (contador reiniciado)?")

S = "s24b-deposito-fallido"
bloquear(S)
m("DEPOSITO;AC-0001;0", S, "depósito fallido (E303) a la cuenta bloqueada")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras depósito fallido: ¿sigue E510?")
m("DEPOSITO;AC-0002;10", S, "depósito exitoso a OTRA cuenta")
m("TRANSFER;AC-0001;AC-0002;100", S, "¿un depósito a otra cuenta desbloquea AC-0001? (no debería)")
