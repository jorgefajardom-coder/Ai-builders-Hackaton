"""Modelo del control (ajustado con exp02). h = Σ v(c)·10^k mod 97 sobre los argumentos alfanuméricos;
control = (94·h + K[cmd]) mod 97. v(dígito)=d+68, v(letra mayúscula)=ord-65+53."""
P = 97
K = {"CONSULTA": 53, "DEPOSITO": 43, "TRANSFER": 43, "ANULA": 71}

def h(args):
    x = 0
    for ch in args:
        if ch.isdigit():
            v = int(ch) + 68
        elif ch.isalpha():
            v = ord(ch.upper()) - 65 + 53
        else:
            continue
        x = (x * 10 + v) % P
    return x

def control(body):
    cmd, args = body.split(";", 1)
    return (94 * h(args) + K[cmd.upper()]) % P
