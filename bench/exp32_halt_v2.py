"""Exp 32 — HALT confirmado en v2: ¿sigue igual que en v1 (exp25)? Autorizado por el usuario.

Solo token personal; termina con /__reset para reactivarlo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import call, msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


S = "s32-halt-v2"
reset(S)
m("ALTA;Ana", S, "estado previo: AC-0001")
m("HALT;01", S, "v2: HALT;01 ¿sigue sin confirmar (E520)?")
m("HALT;1", S, "v2: HALT;1 ¿sigue confirmando (503 E599 'service halted')?")
show(msg("PING;64", S, "v2 tras HALT;1: ¿PING da E599?"))
m("CONSULTA;AC-0001", S, "v2 tras HALT;1: ¿CONSULTA da E599?")
show(call("GET", "/health", seq=S, hipotesis="v2 tras HALT;1: ¿/health sigue 200?"))
show(reset(S, "v2 tras HALT;1: ¿/__reset reactiva?"))
show(msg("PING;64", S, "v2 tras el reset: ¿pong?"))
