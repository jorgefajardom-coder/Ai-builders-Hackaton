"""Exp 05 — Validación predictiva de la fórmula del control (ISO 7064 mod 97-10, letras A=1..Z=26).

Cada mensaje es nuevo (no aparece en el log) y lleva el control que predice control_model.control().
Si la fórmula es correcta, ninguno debe dar E202. Se incluyen también algunos controles predichos +1
(deben dar E202) para descartar que el servicio acepte cualquier cosa.
"""
from control_model import control
from prober import msg, reset, show

S = "s5-formula"
reset(S, "estado limpio: predicciones de la fórmula del control sobre mensajes nuevos")

PRED = [
    ("ALTA;maria", "ALTA con nombre en minúsculas (letras J..Z de dos cifras: r)"),
    ("ALTA;Xavier", "ALTA con mayúsculas/minúsculas mezcladas"),
    ("ALTA;Quintanilla", "ALTA con nombre largo de letras J..Z"),
    ("consulta;AC-0001", "comando en minúsculas: misma cifra que en mayúsculas"),
    ("DEPOSITO;AC-0001;98765", "DEPOSITO a cuenta recién creada"),
    ("TRANSFER;AC-0001;AC-0002;1234", "TRANSFER entre las dos cuentas creadas"),
    ("ANULA;OP-0002", "ANULA de la transferencia"),
    ("CONSULTA;AC-0002", "CONSULTA de la cuenta destino"),
    ("CONSULTA;KLMNOP", "CONSULTA con letras de dos cifras (K=11..P=16)"),
    ("Deposito;ZZ-9;1", "comando capitalizado y cuenta con letras altas"),
]
for body, why in PRED:
    c = control(body)
    e = msg(f"{body};{c}", S,
            f"la fórmula 98-(N·100 mod 97) con A=1..Z=26 concatenadas predice {c} para '{body}' ({why}); no debe dar E202")
    show(e)
    ok = not (isinstance(e["response"], dict) and e["response"].get("error") in ("E201", "E202"))
    print("   ->", "ACIERTO" if ok else "FALLO")

for body in ["CONSULTA;AC-0001", "ALTA;maria"]:
    c = control(body) % 98 + 1 if control(body) < 98 else 2
    e = msg(f"{body};{c}", S, f"control predicho+1 ({c}) para '{body}' debe ser rechazado con E202")
    show(e)
