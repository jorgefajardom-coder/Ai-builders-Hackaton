"""Exp 22 — Bloqueo antifraude: "3 transferencias fallidas = cuenta bloqueada" (dato de otro equipo, sin evidencia propia).

Preguntas: ¿existe? ¿qué fallos cuentan (E507, E506, E304, E303, E401)? ¿a qué cuenta bloquea (origen/destino)?
¿una transferencia exitosa reinicia el contador? ¿qué operaciones quedan bloqueadas y con qué error?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


def base(seq):
    reset(seq)
    m("ALTA;Ana", seq, "AC-0001")
    m("ALTA;Beto", seq, "AC-0002")
    m("DEPOSITO;AC-0001;1000", seq, "saldo 1000 en AC-0001")


# A: 3 fallos por saldo insuficiente (E507) y luego una transferencia válida
S = "s22a-e507"
base(S)
for i in range(1, 4):
    m("TRANSFER;AC-0001;AC-0002;5000", S, f"fallo E507 #{i} desde AC-0001")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras 3 E507: ¿transferencia válida bloqueada?")
m("TRANSFER;AC-0001;AC-0002;100", S, "¿el bloqueo persiste?")
m("CONSULTA;AC-0001", S, "¿CONSULTA de la cuenta bloqueada funciona?")
m("DEPOSITO;AC-0001;10", S, "¿DEPOSITO a la cuenta bloqueada funciona?")
m("TRANSFER;AC-0002;AC-0001;10", S, "¿se puede transferir HACIA la cuenta bloqueada?")
m("ANULA;OP-0001", S, "¿ANULA de una operación de la cuenta bloqueada funciona?")

# B: solo 2 fallos → no debería bloquear
S = "s22b-dos"
base(S)
for i in range(1, 3):
    m("TRANSFER;AC-0001;AC-0002;5000", S, f"fallo E507 #{i}")
m("TRANSFER;AC-0001;AC-0002;100", S, "con 2 fallos: ¿transferencia válida pasa?")

# C: 2 fallos, 1 éxito, 1 fallo → ¿el éxito reinicia el contador?
S = "s22c-reinicio"
base(S)
for i in range(1, 3):
    m("TRANSFER;AC-0001;AC-0002;5000", S, f"fallo E507 #{i}")
m("TRANSFER;AC-0001;AC-0002;100", S, "éxito intermedio")
m("TRANSFER;AC-0001;AC-0002;5000", S, "fallo tras el éxito: ¿3er fallo acumulado o 1º tras reinicio?")
m("TRANSFER;AC-0001;AC-0002;100", S, "¿bloqueada (contador acumulado) o pasa (reinicio)?")

# D: fallos E506 (límite) cuentan?
S = "s22d-e506"
base(S)
for i in range(1, 4):
    m("TRANSFER;AC-0001;AC-0002;100001", S, f"fallo E506 #{i}")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras 3 E506: ¿bloqueada?")

# E: fallos E401 (destino inexistente) y E304 (misma cuenta) y E303 (monto) cuentan?
S = "s22e-otros"
base(S)
m("TRANSFER;AC-0001;AC-0009;10", S, "fallo E401 #1")
m("TRANSFER;AC-0001;AC-0009;10", S, "fallo E401 #2")
m("TRANSFER;AC-0001;AC-0009;10", S, "fallo E401 #3")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras 3 E401: ¿bloqueada?")
S = "s22f-e304-e303"
base(S)
m("TRANSFER;AC-0001;AC-0001;10", S, "fallo E304 #1")
m("TRANSFER;AC-0001;AC-0001;10", S, "fallo E304 #2")
m("TRANSFER;AC-0001;AC-0001;10", S, "fallo E304 #3")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras 3 E304: ¿bloqueada?")
m("TRANSFER;AC-0001;AC-0002;0", S, "fallo E303 #1")
m("TRANSFER;AC-0001;AC-0002;0", S, "fallo E303 #2")
m("TRANSFER;AC-0001;AC-0002;0", S, "fallo E303 #3")
m("TRANSFER;AC-0001;AC-0002;100", S, "tras 3 E303: ¿bloqueada?")
