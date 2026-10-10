"""Exp 19 — Desempate de la sugerencia entre ALTA y ANULA (ambas a distancia 2 de 'NLA')."""
from control_model import control
from prober import msg, reset, show

S = "s19-empate"
reset(S, "estado limpio: desempate de sugerencia")
b = "NLA;AC-0001"
show(msg(f"{b};{control(b)}", S, "'NLA' está a distancia 2 de ALTA y de ANULA: si gana el primero de la lista [ALTA, ...] o el orden alfabético -> ALTA"))
