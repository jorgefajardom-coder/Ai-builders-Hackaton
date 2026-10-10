"""Regresión v1 → v2: reproduce contra el original los casos grabados en la mañana y lista qué cambió.

Cada caso = un POST /__reset + los requests que le siguieron en su secuencia del log. Todo pasa por el
prober (queda en experimentos.jsonl con seq "v2-<seq original>"), y cada respuesta se compara con la
grabada en v1 usando el comparador del jurado. De los barridos grandes (s2-control, s4-letras) se toman
solo los aciertos (respuestas distintas de E202), más 3 fallos de muestra.

Uso:
    python bench/regresion.py                    # todo lo grabado antes del incidente
    python bench/regresion.py --hasta 2700       # solo ids de log <= 2700
    python bench/regresion.py --seq s16-transfer # solo esa secuencia (repetible)
"""
import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prober  # noqa: E402
from diff import same  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BARRIDOS = {"s2-control", "s4-letras"}


def cargar(hasta):
    by_seq = OrderedDict()
    for line in (ROOT / "experimentos.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["id"] > hasta or r["seq"].startswith(("centinela", "v2-")) or r.get("infra"):
            continue
        by_seq.setdefault(r["seq"], []).append(r)
    casos = []
    for seq, rows in by_seq.items():
        cur = None
        for r in rows:
            if r.get("ruta") == "/__reset" and r.get("auth") == "propio" and r.get("status") == 200:
                if cur:
                    casos.append((seq, cur))
                cur = []
            elif cur is not None and r.get("auth") != "literal":   # el header literal no quedó en el log
                cur.append(r)
        if cur:
            casos.append((seq, cur))
    out = []
    for seq, pasos in casos:
        if seq in BARRIDOS:
            hits = [p for p in pasos if not (isinstance(p["response"], dict) and p["response"].get("error") == "E202")]
            fallos = [p for p in pasos if p not in hits][:3]
            pasos = hits + fallos
        out.append((seq, pasos))
    return out


def enviar(paso, seq):
    hip = f"regresión v2: ¿igual que #{paso['id']} de v1?"
    req = paso["request"]
    if isinstance(req, dict):
        return prober.call(paso["metodo"], paso["ruta"], req, auth=paso["auth"], seq=seq, hipotesis=hip)
    return prober.call(paso["metodo"], paso["ruta"], raw=req, auth=paso["auth"], seq=seq, hipotesis=hip)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", type=int, default=10**9)
    ap.add_argument("--seq", action="append")
    a = ap.parse_args()
    casos = [(s, p) for s, p in cargar(a.hasta) if not a.seq or s in a.seq]
    total = iguales = 0
    cambios = []
    for seq, pasos in casos:
        nseq = "v2-" + seq
        prober.reset(nseq, f"regresión v2: estado limpio para repetir '{seq}'")
        for p in pasos:
            e = enviar(p, nseq)
            total += 1
            if e.get("infra"):
                continue
            if e["status"] == p["status"] and same(e["response"], p["response"]):
                iguales += 1
            else:
                cambios.append({"seq": seq, "v1_id": p["id"], "v2_id": e["id"], "metodo": p["metodo"], "ruta": p["ruta"],
                                "request": p["request"], "v1": [p["status"], p["response"]], "v2": [e["status"], e["response"]]})
    print(f"Regresión: {iguales}/{total} respuestas iguales a v1 · {len(cambios)} distintas")
    for c in cambios:
        req = c["request"] if not isinstance(c["request"], str) or len(c["request"]) < 90 else "(cuerpo grande)"
        print(f"  ✗ [{c['seq']}] v1 #{c['v1_id']} → v2 #{c['v2_id']} {c['metodo']} {c['ruta']} {json.dumps(req, ensure_ascii=False)}\n"
              f"      v1 {c['v1'][0]} {json.dumps(c['v1'][1], ensure_ascii=False)}\n"
              f"      v2 {c['v2'][0]} {json.dumps(c['v2'][1], ensure_ascii=False)}")
    (ROOT / "bench" / "regresion_v2.json").write_text(json.dumps(cambios, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
