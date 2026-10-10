"""Fuzzer diferencial: secuencias aleatorias contra el original (vía prober, quedan en el log) y contra el
reemplazo en proceso (perfil v2), paso a paso, con el comparador del jurado.

Las secuencias imitan las del set oculto (6–12 pasos tras /__reset) y se sesgan hacia lo que crea estado y
casos borde: montos frontera del límite, bloqueos antifraude, anulaciones, saldos negativos, typos, errores
de forma. Reproducible por semilla. Nunca envía HALT;1 (detendría el token a mitad de la corrida).

Uso:
    python bench/fuzz.py --seed 1 --n 60          # 60 secuencias
    python bench/fuzz.py --seed 7 --n 10 --min 6 --max 12
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import prober  # noqa: E402
from app.checkval import control  # noqa: E402
from app.profiles import V2  # noqa: E402
from diff import InProcess, same  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MONTOS = ["1", "5", "10", "100", "999", "1000", "49999", "50000", "50001", "99999", "100000", "100001",
          "250000", "9999999999", "0", "-5", "10.5", "007", "12345678901"]
NOMBRES = ["Ana", "Beto", "José", "ñandú", "a b", "X", "123", "Lucia"]
COMANDOS_RAROS = ["SALDOS", "CONSULTX", "TRANSFERIR", "ALT", "NOTA", "DEPOSIT", "ANULAR", "PIN"]


class Gen:
    def __init__(self, rnd):
        self.r = rnd
        self.cuentas = 0
        self.ops = 0

    def cuenta(self, existente=0.85):
        if self.cuentas and self.r.random() < existente:
            return f"AC-{self.r.randint(1, self.cuentas):04d}"
        return f"AC-{self.r.choice([9, 42, 1, 2]):04d}"

    def monto(self):
        return self.r.choice(MONTOS)

    def msg(self, body, ctl=None):
        return {"m": f"{body};{control(body) if ctl is None else ctl}"}

    def paso(self):
        r = self.r.random()
        if self.cuentas < 2 or r < 0.12:
            self.cuentas += 1
            return self.msg(f"ALTA;{self.r.choice(NOMBRES)}"), "ALTA"
        if r < 0.30:
            return self.msg(f"DEPOSITO;{self.cuenta()};{self.monto()}"), "DEPOSITO"
        if r < 0.58:
            a, b = self.cuenta(), self.cuenta()
            if self.r.random() < 0.08:
                b = a
            return self.msg(f"TRANSFER;{a};{b};{self.monto()}"), "TRANSFER"
        if r < 0.72:
            return self.msg(f"CONSULTA;{self.cuenta()}"), "CONSULTA"
        if r < 0.82:
            op = f"OP-{self.r.randint(1, max(1, self.ops + 2)):04d}"
            return self.msg(f"ANULA;{op}"), "ANULA"
        if r < 0.86:
            return {"m": self.r.choice(["PING;64", "PING;XX", "ping;1", "PING;X;XX"])}, "PING"
        if r < 0.88:
            return self.msg("NOTAS"), "NOTAS"
        if r < 0.90:
            return self.msg(f"HALT;{self.r.choice(['x', '0', '01', 'SI'])}"), "HALT"
        if r < 0.94:
            body = f"{self.r.choice(COMANDOS_RAROS)};{self.cuenta()}"
            return self.msg(body), "E301"
        if r < 0.97:
            body = f"CONSULTA;{self.cuenta()}"
            c = control(body)
            return {"m": f"{body};{self.r.choice([c - 1 if c > 2 else c + 1, '0' + str(c), 'XX'])}"}, "CONTROL"
        return self.msg(f"TRANSFER;{self.cuenta()};{self.monto()}"), "ARIDAD"


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--min", type=int, default=6)
    ap.add_argument("--max", type=int, default=12)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    rep = InProcess()
    total = iguales = 0
    malas = []
    for i in range(a.n):
        seq = f"fz{a.seed}-{i:03d}"
        prober.reset(seq, f"fuzz semilla {a.seed}: estado limpio")
        rep.reset()
        g = Gen(rnd)
        primera = None
        for k in range(rnd.randint(a.min, a.max)):
            body, tipo = g.paso()
            e = prober.call("POST", "/msg", body, seq=seq,
                            hipotesis=f"fuzz {tipo} (paso {k + 1}): ¿el original responde igual que el reemplazo v2?")
            st = {"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": body}
            status, resp = rep.send(st, V2)
            if status == 200 and isinstance(resp, dict) and resp.get("operacionId"):
                g.ops += 1
            total += 1
            if e.get("infra"):
                continue
            if e["status"] == status and same(e["response"], resp):
                iguales += 1
            elif primera is None:
                primera = {"seq": seq, "paso": k + 1, "id": e["id"], "tipo": tipo, "request": body,
                           "original": [e["status"], e["response"]], "reemplazo": [status, resp]}
        if primera:
            malas.append(primera)
            print(f"✗ {seq} paso {primera['paso']} ({primera['tipo']}) #{primera['id']} {json.dumps(primera['request'], ensure_ascii=False)}\n"
                  f"    original  {primera['original'][0]} {json.dumps(primera['original'][1], ensure_ascii=False)}\n"
                  f"    reemplazo {primera['reemplazo'][0]} {json.dumps(primera['reemplazo'][1], ensure_ascii=False)}", flush=True)
    print(f"\nFuzz semilla {a.seed}: secuencias {a.n - len(malas)}/{a.n} idénticas · pasos {iguales}/{total}")
    (ROOT / "bench" / f"fuzz_{a.seed}.json").write_text(json.dumps(malas, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
