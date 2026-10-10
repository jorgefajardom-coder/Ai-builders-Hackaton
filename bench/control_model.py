"""Modelo del control (check value) del servicio original — ISO 7064 mod 97-10 estilo IBAN.

Mensaje: CMD;arg1;...;argN;CONTROL. El cuerpo es todo lo anterior al último ';' (comando incluido).

    N       = concatenación decimal de cada carácter alfanumérico ASCII del cuerpo:
              dígito -> el mismo dígito; letra (sin distinguir mayúsculas) -> su posición
              alfabética A=1 .. Z=26 escrita en decimal (J..Z ocupan DOS posiciones).
              ';' '-' y demás caracteres no cuentan (ver exp05 para espacios / unicode).
    control = 98 - (N * 100 mod 97)          -> rango 2..98 (98 cuando N*100 ≡ 0)

Evidencia: ajuste offline 38/38 pares válidos del log (fit_alfa.py: ids 37, 169, 178, 203, 291,
330, 405, 482, 565, 638, 701, 737, 740-744, 797, 875, 950, 1007, 1061, 1160, 1247 + ejemplos)
y predicciones en mensajes no vistos (exp05_formula.py, ver docs/01 Problema/Hallazgos exploración.md).
El modelo anterior (d+68, letras ord-12, constante por comando) estaba sobreajustado y fue descartado.
"""


def digits(body: str) -> str:
    out = []
    for ch in body:
        if '0' <= ch <= '9':
            out.append(ch)
        elif 'A' <= ch.upper() <= 'Z' and ch.isascii():
            out.append(str(ord(ch.upper()) - 64))
    return ''.join(out)


def control(body: str) -> int:
    r = 0
    for d in digits(body):  # N mod 97 incremental (evita enteros gigantes)
        r = (r * 10 + int(d)) % 97
    return 98 - (r * 100) % 97


def is_valid(msg: str) -> bool:
    body, sep, c = msg.rpartition(';')
    if not sep or not c.isdigit():
        return False
    return int(c) == control(body)


if __name__ == '__main__':
    import sys
    for b in sys.argv[1:]:
        print(b, control(b))
