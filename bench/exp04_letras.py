"""Exp 04 — Valor de cada carácter en el control: barrido sobre 'CONSULTA;<c>' y despeje de v(c)."""
import sys
from exp02_control import find_control
from prober import reset
import exp02_control
exp02_control.S = S = "s4-letras"
P = 97
inv94 = pow(94, -1, P)
reset(S)
for ch in sys.argv[1]:
    c, e = find_control(f"CONSULTA;{ch}")
    v = None if c is None else ((c - 53) * inv94) % P
    print(f"== '{ch}' control={c} v={v} resp={e['response'] if e else None}")
