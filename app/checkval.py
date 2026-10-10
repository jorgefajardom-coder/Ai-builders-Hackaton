"""Valor de control: ISO 7064 mod 97-10 estilo IBAN (spec I-01, confirmado: log 1249–1260, ajuste 38/38).

N = concatenación decimal de cada carácter alfanumérico ASCII del cuerpo (comando incluido):
dígitos tal cual; letras sin distinguir mayúsculas como A=1 … Z=26 (J..Z ocupan dos posiciones).
control = 98 − (N·100 mod 97). Misma fórmula que bench/control_model.py.
"""


def _digits(body: str):
    for ch in body:
        if "0" <= ch <= "9":
            yield int(ch)
        elif ch.isascii() and "A" <= ch.upper() <= "Z":
            for d in str(ord(ch.upper()) - 64):
                yield int(d)


def control(body: str) -> int:
    r = 0
    for d in _digits(body):
        r = (r * 10 + d) % 97
    return 98 - (r * 100) % 97
