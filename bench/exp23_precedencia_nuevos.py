"""Exp 23 — Precedencia de E510 (cuenta bloqueada) y validación de control/sugerencias para HALT y NOTAS.

No se prueba ninguna "confirmación" de HALT: es destructivo y podría detener el original compartido.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip, ctl=None):
    show(msg(f"{body};{control(body) if ctl is None else ctl}", seq, hip))


S = "s23a-e510-orden"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0001;1000", S, "saldo 1000")
for i in range(1, 4):
    m("TRANSFER;AC-0001;AC-0002;5000", S, f"E507 #{i} para bloquear AC-0001")
m("TRANSFER;AC-0001;AC-0002;0", S, "bloqueada + monto inválido: ¿E303 o E510 primero?")
m("TRANSFER;AC-0001;AC-0001;10", S, "bloqueada + origen=destino: ¿E304 o E510?")
m("TRANSFER;AC-0001;AC-0009;10", S, "bloqueada + destino inexistente: ¿E401 o E510?")
m("TRANSFER;AC-0001;AC-0002;100001", S, "bloqueada + sobre el límite: ¿E506 o E510?")
m("TRANSFER;AC-0001;AC-0002;5000", S, "bloqueada + saldo insuficiente: ¿E507 o E510?")
m("TRANSFER;AC-0001;AC-0002", S, "bloqueada + aridad: ¿E302 o E510?")
m("TRANSFER;AC-0002;AC-0001;10", S, "AC-0002 sin saldo → E507 (1er fallo de AC-0002; destino bloqueado no importa)")
m("CONSULTA;AC-0001", S, "saldo de la bloqueada intacto")

S = "s23b-halt-notas-control"
reset(S)
m("NOTAS", S, "NOTAS con control no numérico: ¿lo ignora como PING o E201?", ctl="XX")
m("NOTAS", S, "NOTAS con control incorrecto: ¿E202?", ctl=control("NOTAS") % 97 + 1)
m("HALT;hola", S, "HALT con control no numérico: ¿E201?", ctl="XX")
m("HALT;hola", S, "HALT con control incorrecto: ¿E202?", ctl=control("HALT;hola") % 97 + 1)
m("HALT;hola", S, "HALT con argumento arbitrario (no cuenta): ¿mismo 409 E520?")
m("HALT;AC-0009", S, "HALT con cuenta inexistente: ¿E401 o 409 E520?")
m("NOTA", S, "sugerencia: NOTA → ¿sugerencia NOTAS?")
m("HALTS;x", S, "sugerencia: HALTS → ¿sugerencia HALT?")
m("NOTAS", S, "NOTAS es estática: segunda llamada igual")
