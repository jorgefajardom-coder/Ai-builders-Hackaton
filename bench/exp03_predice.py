"""Exp 03 — Validación predictiva del modelo de control: un request por mensaje nuevo."""
from control_model import control
from prober import msg, reset, show
S = "s3-prediccion"
reset(S)
for body in ["CONSULTA;ZZ-9876", "CONSULTA;AC-4242", "ANULA;OP-0042", "ANULA;XY-123",
             "DEPOSITO;AC-0777;31415", "TRANSFER;AC-0003;AC-0004;999", "TRANSFER;QQ-1;RR-2;5"]:
    c = control(body)
    e = msg(f"{body};{c}", S, f"el modelo de control predice {c} para '{body}' (no debe dar E202)")
    show(e)
    print("   ->", "ACIERTO" if e["response"].get("error") != "E202" else "FALLO")
