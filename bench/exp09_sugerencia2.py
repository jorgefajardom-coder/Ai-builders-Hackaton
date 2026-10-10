"""Exp 09 — Sugerencia: Levenshtein vs Damerau, desempates y comandos muy cortos."""
from control_model import control
from prober import msg, reset, show

S = "s9-sugerencia2"
reset(S, "estado limpio: detalles de la sugerencia")

CMDS = [
    ("OCNSUTLA", "dos transposiciones: Levenshtein 4 (sin sugerencia) vs Damerau/OSA 2 (sugiere CONSULTA)"),
    ("PITA", "empate a distancia 2 entre PING y ALTA: ¿cuál gana? revela el orden de la lista"),
    ("ANLA", "ANULA a distancia 1 y ALTA a distancia 2: debe ganar la mínima (ANULA)"),
    ("AL", "distancia 2 a ALTA con comando de 2 letras: ¿sugiere?"),
    ("A", "distancia 3 a ALTA: sin sugerencia"),
    ("PINGPING", "distancia 4 a PING: sin sugerencia"),
    ("DEPOSITOO", "DEPOSITO + O: sugiere DEPOSITO"),
    ("TRANSFE", "TRANSFER truncado en 1"),
    ("ÁLTA", "letra acentuada Á (no ASCII, no cuenta en el control): distancia 1 a ALTA"),
]
for cmd, why in CMDS:
    body = f"{cmd};AC-0001"
    show(msg(f"{body};{control(body)}", S, f"'{cmd}': {why}"))
