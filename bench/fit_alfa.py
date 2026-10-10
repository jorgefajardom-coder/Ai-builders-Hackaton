"""Ajuste offline del control: cada carácter se convierte a una cadena decimal y se concatena (estilo IBAN).

Modos de letra: 'pos' A=1..Z=26, 'b36' A=10..Z=35, 'ord' código ASCII. Comando incluido o no.
Busca la constante k tal que control = (k - N*100) mod 97 encaja con todos los pares válidos del log.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_pairs():
    pairs = {}
    srcs = [ROOT / 'material/pruebas/ejemplos.jsonl', ROOT / 'experimentos.jsonl']
    for src in srcs:
        for l in open(src, encoding='utf-8'):
            e = json.loads(l)
            if e.get('ruta', '/msg') != '/msg' or not isinstance(e['request'], dict):
                continue
            m = e['request'].get('m')
            if not isinstance(m, str):
                continue
            r = e['response']
            if not isinstance(r, dict) or r.get('error') in ('E202', 'E201', 'E001', 'E404', 'E101', 'E102', 'E103'):
                continue
            b, _, c = m.rpartition(';')
            if b and c.isdigit() and not b.upper().startswith('PING'):
                pairs[b] = (int(c), e['id'])
    return pairs


def digits(s, mode):
    out = ''
    for ch in s:
        if ch.isdigit():
            out += ch
        elif ch.isalpha():
            if mode == 'pos':
                out += str(ord(ch.upper()) - 64)
            elif mode == 'b36':
                out += str(ord(ch.upper()) - 55)
            elif mode == 'ord':
                out += str(ord(ch))
    return out


def n_of(body, mode, cmd):
    if cmd == 'sin':
        body = body.split(';', 1)[1] if ';' in body else ''
    return int(digits(body, mode) or '0')


if __name__ == '__main__':
    pairs = load_pairs()
    print(len(pairs), 'pares')
    for mode in ('pos', 'b36', 'ord'):
        for cmd in ('con', 'sin'):
            best = max(range(97), key=lambda k: sum((k - n_of(b, mode, cmd) * 100 - c) % 97 == 0 for b, (c, _) in pairs.items()))
            ok = sum((best - n_of(b, mode, cmd) * 100 - c) % 97 == 0 for b, (c, _) in pairs.items())
            print(mode, cmd, 'k=', best, ok, '/', len(pairs))
    if len(sys.argv) > 1:
        mode, cmd, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
        for b, (c, i) in pairs.items():
            p = (k - n_of(b, mode, cmd) * 100) % 97
            print(i, b, c, p, 'OK' if (p - c) % 97 == 0 else 'FALLA')
