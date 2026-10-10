"""Exp 12 — Límite de tamaño del mensaje / nombre (E101?). Búsqueda acotada: 5000, 100000, y si
hay corte, bisección corta sobre la longitud del nombre."""
import sys
from control_model import control
from prober import msg, reset, show

S = "s12-tamano"
reset(S, "estado limpio: límites de tamaño")


def alta(n, why):
    body = "ALTA;" + "C" * n
    e = msg(f"{body};{control(body)}", S, f"ALTA con nombre de {n} letras (mensaje {len(body) + 3} chars): {why}")
    print(n, e["id"], e["status"], e["response"])
    return e


for n in [int(x) for x in sys.argv[1:]] or [5000, 100000]:
    alta(n, "¿se acepta (201) o hay límite de longitud (E10x / 413)?")


def bisect(lo, hi):
    """lo aceptado, hi rechazado -> frontera exacta de la longitud del nombre."""
    while hi - lo > 1:
        mid = (lo + hi) // 2
        e = alta(mid, f"bisección del límite entre {lo} (201) y {hi} (413)")
        if e["status"] == 413:
            hi = mid
        else:
            lo = mid
    print("frontera: nombre", lo, "ok;", hi, "rechazado")


if __name__ == "__main__" and len(sys.argv) == 1:
    bisect(5000, 100000)
