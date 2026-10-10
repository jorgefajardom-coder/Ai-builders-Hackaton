"""Exp 35 — ¿El límite de TRANSFER no aplica entre cuentas del mismo titular (mismo nombre en ALTA)?

exp33 (Ana→Beto) siempre E506 sobre el límite; exp34 (Lucia→Lucia) E507 incluso sin historia. Hipótesis:
entre cuentas con el mismo nombre no hay límite por operación, así que solo falla el saldo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


def caso(nombre, n1, n2, saldo, monto, hip):
    S = f"s35-{nombre}"
    reset(S, f"exp35 {nombre}: estado limpio")
    m(f"ALTA;{n1}", S, f"AC-0001 titular '{n1}' (origen)")
    m(f"ALTA;{n2}", S, f"AC-0002 titular '{n2}' (destino)")
    if saldo:
        m(f"DEPOSITO;AC-0001;{saldo}", S, f"saldo origen {saldo}")
    m(f"TRANSFER;AC-0001;AC-0002;{monto}", S, hip)
    m("CONSULTA;AC-0002", S, f"{nombre}: saldo del destino tras la transferencia")


caso("igual-con-saldo", "Lucia", "Lucia", 1000000, 100001, "mismo titular, saldo de sobra, 100001: ¿200 (sin límite) o E506?")
caso("igual-sin-saldo", "Lucia", "Lucia", 0, 50001, "mismo titular, sin saldo, 50001: ¿E507 (sin límite)?")
caso("distinto-con-saldo", "Lucia", "Mateo", 1000000, 100001, "titulares distintos, saldo de sobra, 100001: ¿E506?")
caso("igual-otro-nombre", "Ana", "Ana", 1000000, 50001, "mismo titular 'Ana': ¿también sin límite (regla general, no del nombre Lucia)?")
caso("mayusculas", "Ana", "ANA", 1000000, 50001, "'Ana' vs 'ANA': ¿se consideran el mismo titular?")
