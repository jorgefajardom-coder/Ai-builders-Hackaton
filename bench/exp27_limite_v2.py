"""Exp 27 — Incidente v2: nuevo límite por operación de TRANSFER (CB-05).

En v2 TRANSFER de 100000 da E506 (log 3452, 3506, 3527) y 40000 pasa (log 3504). Búsqueda binaria del
máximo permitido L en (40000, 100000). Cada E506 suma al antifraude, así que tras cada E506 se hace una
TRANSFER de 1 (éxito → reinicia el contador) para no bloquear la cuenta durante la búsqueda.
Después: ¿inclusivo? ¿por operación o acumulado? ¿depende del saldo? ¿E506 antes que E507? ¿sigue contando
para el bloqueo (3 E506 → E510)?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    e = msg(f"{body};{control(body)}", seq, hip)
    show(e)
    return e


def err(e):
    return e["response"].get("error") if isinstance(e["response"], dict) else None


S = "s27a-limite-busqueda"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0001;9999999999", S, "saldo grande en AC-0001 para que E507 no interfiera")


def prueba(x):
    e = m(f"TRANSFER;AC-0001;AC-0002;{x}", S, f"v2 límite: ¿TRANSFER de {x} pasa (200) o E506?")
    if err(e) == "E506":
        m("TRANSFER;AC-0001;AC-0002;1", S, "éxito de 1 para reiniciar el contador antifraude tras el E506")
        return False
    assert e["status"] == 200, e
    return True


lo, hi = 40000, 100000          # lo pasa, hi da E506
for x in (50000, 50001):        # primero el candidato redondo
    if prueba(x):
        lo = x
    else:
        hi = x
        break
while hi - lo > 1:
    mid = (lo + hi) // 2
    if prueba(mid):
        lo = mid
    else:
        hi = mid
L = lo
print(f"==> máximo permitido L = {L}; L+1 = {hi} da E506")

S = "s27b-limite-semantica"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m(f"DEPOSITO;AC-0001;{L}", S, f"saldo exactamente L={L}")
m(f"TRANSFER;AC-0001;AC-0002;{L + 1}", S, f"v2: L+1 con saldo L → ¿E506 antes que E507? (orden v1: E506 → E507)")
m(f"TRANSFER;AC-0001;AC-0002;{L}", S, f"v2: L exacto con saldo L → 200 (inclusivo, no depende del saldo)")
m(f"DEPOSITO;AC-0001;{3 * L}", S, f"recargar 3·L")
m(f"TRANSFER;AC-0001;AC-0002;{L}", S, "v2: segunda TRANSFER de L seguida → 200 si el límite es por operación")
m(f"TRANSFER;AC-0001;AC-0002;{L}", S, "v2: tercera TRANSFER de L → 200 (no acumulado)")
m("CONSULTA;AC-0002", S, f"v2: AC-0002 recibió 3·L")
m(f"DEPOSITO;AC-0002;{L + 1}", S, "v2: DEPOSITO por encima del límite de TRANSFER → 200 (sin límite)")

S = "s27c-limite-antifraude"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0001;1000000", S, "saldo 1000000")
for i in range(1, 4):
    m(f"TRANSFER;AC-0001;AC-0002;{L + 1}", S, f"v2: E506 #{i} con el nuevo límite (¿cuenta para el bloqueo?)")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: tras 3 E506 → ¿E510 423 con intentos 1?")
