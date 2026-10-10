"""Exp 33 — ¿Cuándo gana E507 sobre E506 en v2? (diferencia encontrada por el fuzzer, log 4246)

Evidencia en conflicto: saldo 50000 + TRANSFER 50001 → E506 (log 3747); saldo 0 + TRANSFER 100001 → E507 (log 4246).
Cada caso arranca de un estado limpio con una sola cuenta origen con saldo S, para aislar la regla.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


CASOS = [  # (saldo origen, monto, qué distingue)
    (0, 50001, "saldo 0 y monto apenas sobre el límite: ¿E507 (depende del saldo) o E506 (depende del monto)?"),
    (0, 100001, "repite log 4246 sin fallo previo: ¿E507 también sin contador de fallos?"),
    (49999, 50001, "saldo justo bajo el límite: ¿E507?"),
    (50000, 50001, "repite log 3747: ¿E506?"),
    (50000, 100001, "saldo = límite, monto > 100000: ¿E506 o E507?"),
    (100000, 100001, "saldo 100000, monto 100001: ¿E506 o E507?"),
    (1000000, 100001, "saldo de sobra: ¿E506?"),
    (1, 2, "control: saldo insuficiente bajo el límite → E507"),
]

for i, (saldo, monto, hip) in enumerate(CASOS):
    S = f"s33-{i}"
    reset(S, f"exp33 caso {i}: estado limpio")
    m("ALTA;Ana", S, "AC-0001 (origen)")
    m("ALTA;Beto", S, "AC-0002 (destino)")
    if saldo:
        m(f"DEPOSITO;AC-0001;{saldo}", S, f"saldo de origen = {saldo}")
    m(f"TRANSFER;AC-0001;AC-0002;{monto}", S, f"saldo {saldo}, monto {monto}: {hip}")
