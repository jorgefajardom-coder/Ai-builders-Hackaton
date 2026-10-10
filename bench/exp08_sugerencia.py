"""Exp 08 — Regla del campo 'sugerencia' en E301 (visto en log 1307, 1309, 1310 con espacios).

Hipótesis candidatas: (a) se sugiere si el comando recortado/normalizado coincide con uno conocido;
(b) se sugiere si la distancia de edición a un comando conocido es <= 1 o 2.
Todos los mensajes llevan control válido para que el error sea E301.
"""
from control_model import control
from prober import msg, reset, show

S = "s8-sugerencia"
reset(S, "estado limpio: regla de sugerencia en E301")

CMDS = [
    ("CONSULTAS", "un carácter de más al final (distancia 1)"),
    ("CONSULT", "un carácter de menos (distancia 1)"),
    ("CONSULTX", "una sustitución (distancia 1)"),
    ("CNSULTA", "una letra borrada en medio (distancia 1)"),
    ("CONSUTLA", "transposición (distancia 2 Levenshtein, 1 Damerau)"),
    ("XONSULTX", "dos sustituciones (distancia 2)"),
    ("XXNSULTX", "tres sustituciones (distancia 3)"),
    ("PONG", "PING con una sustitución"),
    ("PIN", "PING truncado"),
    ("ALTAS", "ALTA + S"),
    ("ALT", "ALTA truncado"),
    ("SALDO", "comando inexistente sin parecido (distancia grande a todos)"),
    ("consultas", "minúsculas + 1 de más: ¿la sugerencia sale en mayúsculas?"),
    ("C ONSULTA", "espacio interno: ¿se ignoran espacios al comparar?"),
    ("\tPING", "tabulador inicial: ¿trim de todo espacio en blanco?"),
    ("DEPOSITOS", "DEPOSITO + S"),
    ("ANULAR", "ANULA + R"),
    ("TRANSFERIR", "TRANSFER + IR (distancia 2)"),
]
for cmd, why in CMDS:
    body = f"{cmd};AC-0001"
    show(msg(f"{body};{control(body)}", S, f"'{cmd}': {why}; control válido -> E301; ¿incluye sugerencia?"))
