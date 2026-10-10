"""Exp 26 — Incidente v2: formato del saldo en CONSULTA (CB-04).

La regresión (log 3394–3547) mostró que en v2 CONSULTA devuelve el saldo como string con 2 decimales y
dividido por 100 (los montos son centavos). Preguntas: ¿siempre 2 decimales? ¿separador de miles? ¿valores
grandes? ¿negativos pequeños (−0.05)? ¿cambió la ENTRADA de montos (siguen enteros, E303 para decimales)?
¿DEPOSITO tiene ahora límite?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


S = "s26a-saldo-formato"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("CONSULTA;AC-0001", S, "v2: saldo 0 → \"0.00\" (string, 2 decimales)")
m("DEPOSITO;AC-0001;1", S, "depósito de 1 centavo")
m("CONSULTA;AC-0001", S, "v2: 1 → \"0.01\" (cero a la izquierda y 2 decimales)")
m("DEPOSITO;AC-0001;9", S, "+9 → saldo 10")
m("CONSULTA;AC-0001", S, "v2: 10 → \"0.10\" (sin recortar el cero final)")
m("DEPOSITO;AC-0001;90", S, "+90 → saldo 100")
m("CONSULTA;AC-0001", S, "v2: 100 → \"1.00\"")
m("DEPOSITO;AC-0001;123456", S, "+123456 → saldo 123556")
m("CONSULTA;AC-0001", S, "v2: 123556 → \"1235.56\" (¿sin separador de miles?)")
m("DEPOSITO;AC-0001;9999999999", S, "v2: ¿DEPOSITO sigue sin límite? monto máximo de 10 cifras")
m("CONSULTA;AC-0001", S, "v2: 10000123555 → \"100001235.55\" (¿separadores de miles, notación exponencial?)")
m("DEPOSITO;AC-0001;9999999999", S, "segundo depósito máximo: saldo 20000123554")
m("CONSULTA;AC-0001", S, "v2: 20000123554 → \"200001235.54\"")

S = "s26b-saldo-negativo"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0002;5", S, "OP-0001: 5 centavos a AC-0002")
m("TRANSFER;AC-0002;AC-0001;5", S, "OP-0002: AC-0002 → AC-0001 los 5")
m("ANULA;OP-0001", S, "anular el depósito deja AC-0002 en −5 (ANULA no verifica saldo)")
m("CONSULTA;AC-0002", S, "v2: −5 → \"-0.05\" (signo y cero a la izquierda)")
m("CONSULTA;AC-0001", S, "v2: 5 → \"0.05\"")
m("ANULA;OP-0002", S, "anular la transferencia: AC-0002 vuelve a 0, AC-0001 a 0")
m("CONSULTA;AC-0002", S, "v2: 0 tras volver de negativo → \"0.00\" (¿\"-0.00\"?)")
m("consulta;AC-0001", S, "v2: comando en minúsculas, mismo formato \"0.00\"")

S = "s26c-monto-entrada"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0001;10.50", S, "v2: ¿el monto de entrada acepta decimales ahora? (v1: E303)")
m("DEPOSITO;AC-0001;1.5", S, "v2: decimal con 1 cifra → ¿E303?")
m("DEPOSITO;AC-0001;0.50", S, "v2: decimal menor que 1 → ¿E303?")
m("DEPOSITO;AC-0001;10000000000", S, "v2: 11 cifras → ¿sigue E303?")
m("DEPOSITO;AC-0001;007", S, "v2: ceros a la izquierda → ¿sigue E303?")
m("DEPOSITO;AC-0001;250", S, "v2: entero válido → 200 (los montos siguen siendo centavos enteros)")
m("TRANSFER;AC-0001;AC-0002;1.00", S, "v2: TRANSFER con decimales → ¿E303?")
m("TRANSFER;AC-0001;AC-0002;250", S, "v2: transferir exactamente el saldo (250) → 200")
m("CONSULTA;AC-0001", S, "v2: saldo 0 → \"0.00\"")
m("CONSULTA;AC-0002", S, "v2: saldo 250 → \"2.50\"")
m("CONSULTA;AC-0009", S, "v2: cuenta inexistente sigue E401 (sin cambio)")
