"""Exp 34 — ¿Qué historia previa hace que TRANSFER 100001 dé E507 en vez de E506? (log 4246 vs exp33)

En estado limpio siempre da E506 (exp33). En fz2-001 la cuenta origen tenía antes un E303 (misma cuenta,
monto 0) y un E507 (1000 sin saldo), con NOTAS y CONSULTA en medio. Se aísla cada ingrediente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


def caso(nombre, previos, final="TRANSFER;AC-0002;AC-0001;100001", repetir=1):
    S = f"s34-{nombre}"
    reset(S, f"exp34 {nombre}: estado limpio")
    m("ALTA;Lucia", S, "AC-0001")
    m("ALTA;Lucia", S, "AC-0002 (origen, saldo 0)")
    for body, hip in previos:
        m(body, S, hip)
    for k in range(repetir):
        m(final, S, f"{nombre}: tras la historia, ¿E506 (como en limpio) o E507 (como log 4246)? intento {k + 1}")


caso("replica", [("TRANSFER;AC-0002;AC-0002;0", "E303 previo"), ("TRANSFER;AC-0002;AC-0001;1000", "E507 previo"),
                 ("NOTAS", "NOTAS"), ("CONSULTA;AC-0002", "CONSULTA")])
caso("solo-e507", [("TRANSFER;AC-0002;AC-0001;1000", "un E507 previo desde el origen")], repetir=2)
caso("solo-e303", [("TRANSFER;AC-0002;AC-0002;0", "un E303 previo")])
caso("solo-e506", [("TRANSFER;AC-0002;AC-0001;50001", "un E506 previo desde el origen")], repetir=2)
caso("e507-otra-cuenta", [("TRANSFER;AC-0001;AC-0002;1000", "E507 previo desde OTRA cuenta (AC-0001)")])
caso("e507-y-exito", [("TRANSFER;AC-0002;AC-0001;1000", "E507 previo"), ("DEPOSITO;AC-0002;500", "depósito"),
                      ("TRANSFER;AC-0002;AC-0001;100", "éxito: reinicia el contador")])
