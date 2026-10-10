"""Exp 25 — HALT confirmado (reportado en fix/two-fixes): ¿HALT;1 detiene el servicio solo para el token?

Autorizado por el usuario. Se usa solo el token personal, y se termina con /__reset para recuperarlo.
Orden de menor a mayor riesgo: variantes que NO deberían confirmar → HALT;1 → efectos → reset.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import call, msg, reset, show  # noqa: E402


def m(body, seq, hip):
    e = msg(f"{body};{control(body)}", seq, hip)
    show(e)
    return e


S = "s25-halt-confirmado"
reset(S)
m("ALTA;Ana", S, "estado previo: AC-0001")
for arg in ["01", "0", "x", "SI"]:
    m(f"HALT;{arg}", S, f"HALT;{arg}: ¿no confirma (E520)?")
m("HALT;1", S, "HALT;1: ¿confirma y detiene (E599 503 'service halted')?")
show(msg("PING;64", S, "tras HALT;1: ¿/msg da E599 también para PING?"))
m("CONSULTA;AC-0001", S, "tras HALT;1: ¿CONSULTA da E599?")
show(msg("esto no es json", S, "tras HALT;1: ¿E599 antes que E100?"))
show(call("GET", "/health", seq=S, hipotesis="tras HALT;1: ¿/health sigue 200?"))
show(call("GET", "/nada", seq=S, hipotesis="tras HALT;1: ¿ruta inexistente sigue 404 E404?"))
show(reset(S, "tras HALT;1: ¿/__reset responde y reactiva el servicio?"))
show(msg("PING;64", S, "tras el reset: ¿PING vuelve a dar pong?"))
m("CONSULTA;AC-0001", S, "tras el reset: el estado se borró (E401)")
