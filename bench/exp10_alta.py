"""Exp 10 — ALTA: reglas del nombre y caracteres no alfanuméricos en el control; formato del id de cuenta.

Control predicho ignorando todo lo que no sea [0-9A-Za-z] ASCII. Si da E202 se registra y se
prueba la alternativa indicada (un request extra).
"""
from control_model import control, digits
from prober import msg, reset, show

S = "s10-alta"
reset(S, "estado limpio: reglas de ALTA y caracteres especiales")


def send(body, why):
    c = control(body)
    e = msg(f"{body};{c}", S, f"{why}; control {c} calculado ignorando lo no alfanumérico ASCII")
    show(e)
    return e


NOMBRES = [
    ("Ana Maria", "nombre con espacio: el espacio no cuenta -> 201 AC-0001"),
    ("José", "nombre con é (no ASCII): si se ignora -> 201"),
    ("O'Brien", "apóstrofo ignorado -> 201"),
    ("R2D2", "dígitos dentro del nombre: cuentan como dígitos -> 201 o error de nombre"),
    ("12345", "nombre solo numérico: ¿se acepta?"),
    ("ñandú", "ñ y ú no ASCII"),
    ("李小龙", "nombre sin ningún carácter que cuente (N=0 -> control de 'ALTA')"),
    ("😀", "emoji como nombre"),
    (" ", "nombre de un solo espacio: ¿segmento vacío E104 o nombre válido?"),
    ("Lucia", "primera Lucia"),
    ("Lucia", "nombre duplicado: ¿nueva cuenta o error?"),
    ("lucia", "duplicado en minúsculas"),
    ("A" * 60, "nombre de 60 letras: ¿límite de longitud?"),
    ("B" * 300, "nombre de 300 letras: ¿límite de longitud?"),
]
for n, why in NOMBRES:
    send(f"ALTA;{n}", f"ALTA '{n[:20]}': {why}")

CUENTAS = [
    ("CONSULTA;AC-0001", "cuenta existente AC-0001 (creada arriba) -> 200 saldo 0"),
    ("CONSULTA;ac-0001", "id en minúsculas: ¿normaliza a AC-0001 o E401?"),
    ("CONSULTA; AC-0001", "espacio antes del id: ¿trim -> 200 o E401?"),
    ("CONSULTA;AC-0001 ", "espacio después del id"),
    ("CONSULTA;AC-1", "id sin ceros de relleno: ¿E401 o formato inválido?"),
    ("CONSULTA;AC-00001", "id con 5 dígitos: ¿equivale a AC-0001?"),
    ("CONSULTA;AC0001", "id sin guion: el guion no cuenta en el control; ¿E401?"),
    ("CONSULTA;AC--0001", "doble guion"),
    ("CONSULTA;XX-0001", "prefijo distinto: ¿E401 o error de formato?"),
    ("CONSULTA;OP-0001", "id de operación usado como cuenta"),
]
for b, why in CUENTAS:
    send(b, why)
