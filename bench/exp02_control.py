"""Exp 02 — Fórmula del control: encontrar el control válido de cuerpos que difieren en un carácter.

Usa CONSULTA sobre cuentas inexistentes: control válido -> E401, inválido -> E202. No muta estado.
"""
import sys
from prober import msg, reset, show

S = "s2-control"


def find_control(body, lo=0, hi=99):
    for c in range(lo, hi + 1):
        e = msg(f"{body};{c}", S, f"barrido de control para '{body}': ¿{c} es válido?")
        err = e["response"].get("error") if isinstance(e["response"], dict) else None
        if err != "E202":
            show(e)
            return c, e
    return None, None


if __name__ == "__main__":
    reset(S)
    bodies = sys.argv[1:] or ["CONSULTA;AC-0000", "CONSULTA;AC-0010", "CONSULTA;AC-0100", "CONSULTA;AC-1000"]
    for b in bodies:
        c, e = find_control(b)
        print(f"== {b} -> control {c}")
