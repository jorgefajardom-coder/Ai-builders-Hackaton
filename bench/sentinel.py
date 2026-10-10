"""Centinela: detecta cambios de comportamiento del original (incidente de las 15:30) de forma continua.

Cada vuelta corre un set fijo de secuencias contra el original (vía prober → quedan en experimentos.jsonl)
y compara cada respuesta con la del reemplazo en proceso (perfil activo, por defecto v1) usando el
comparador del jurado. Toda diferencia = cambio en el original (o hueco del reemplazo).

Uso:
    python bench/sentinel.py                 # vuelta cada 10 min hasta las 20:00
    python bench/sentinel.py --once          # una sola vuelta
    python bench/sentinel.py --every 5       # cada 5 min

Estado legible en docs/04 Ejecución/Centinela.md (lo publica el sitio de documentación).
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prober  # noqa: E402  (carga .env y registra cada request en el log)
from app.checkval import control  # noqa: E402
from diff import InProcess, same  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "docs" / "04 Ejecución" / "Centinela.md"
DAILY_BUDGET_STOP = 7400   # deja margen sobre las 8000 req/día del token
FIN = "20:00"


def ok(body):
    return f"{body};{control(body)}"


def bad(body):
    c = control(body)
    return f"{body};{c - 1 if c > 2 else c + 1}"


def msg_step(m, hip):
    return {"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": {"m": m}, "hip": hip}


def raw_step(raw, hip, metodo="POST", ruta="/msg", auth="propio"):
    return {"metodo": metodo, "ruta": ruta, "auth": auth, "request": raw, "hip": hip}


CASOS = {
    "estado": [
        msg_step(ok("ALTA;Lucia"), "ALTA crea AC-0001"),
        msg_step(ok("ALTA;Mateo"), "ALTA crea AC-0002"),
        msg_step(ok("CONSULTA;AC-0001"), "saldo inicial 0 (cuenta_id snake)"),
        msg_step(ok("DEPOSITO;AC-0001;250000"), "depósito sin límite, 'recieved'"),
        msg_step(ok("TRANSFER;AC-0001;AC-0002;40000"), "transferencia válida"),
        msg_step(ok("TRANSFER;AC-0001;AC-0002;100001"), "límite por operación → E506"),
        msg_step(ok("TRANSFER;AC-0001;AC-0002;100000"), "límite inclusivo 100000"),
        msg_step(ok("CONSULTA;AC-0002"), "saldo destino 140000"),
        msg_step(ok("ANULA;OP-0003"), "ANULA revierte"),
        msg_step(ok("ANULA;OP-0003"), "ANULA repetida → 200 ok:false"),
        msg_step(ok("ANULA;OP-0099"), "operación inexistente → E402"),
        msg_step(ok("TRANSFER;AC-0002;AC-0001;50000"), "saldo insuficiente tras anular → E507"),
        msg_step(ok("TRANSFER;AC-0001;AC-0001;5"), "origen=destino → E304"),
        msg_step(ok("DEPOSITO;AC-0001;0"), "monto 0 → E303"),
        msg_step(ok("DEPOSITO;AC-0002;10.5"), "monto decimal → E303"),
        msg_step(ok("CONSULTA;AC-0009"), "cuenta inexistente → E401"),
        msg_step(ok("CONSULTA;AC-0001"), "saldo final de AC-0001"),
    ],
    "sintaxis": [
        msg_step("PING;64", "PING pong"),
        msg_step("PING;XX", "PING no valida control"),
        msg_step("PING;X;XX", "PING con argumento → E302"),
        msg_step(ok("SALDOS;AC-0001"), "comando desconocido sin sugerencia → E301"),
        msg_step(ok("CONSULTX;AC-0001"), "E301 con sugerencia CONSULTA"),
        msg_step(ok("ALTA;A;B"), "aridad → E302"),
        msg_step(bad("CONSULTA;AC-0001"), "control incorrecto → E202"),
        msg_step("CONSULTA;AC-0001;5X", "control no numérico → E201"),
        msg_step("CONSULTA;AC-0001;014", "control de 3 cifras → E201"),
        msg_step("PING", "sin ';' → E103"),
        msg_step("CONSULTA;;14", "segmento vacío → E104"),
        raw_step("esto no es json", "JSON inválido → E100"),
        raw_step("{}", "sin m → E102"),
        raw_step('{"m": "PING;64"' + " " * 8200 + "}", "cuerpo > 8192 bytes → E101"),
    ],
    "rutas": [
        raw_step(None, "ruta inexistente → E404", metodo="GET", ruta="/nada"),
        raw_step(None, "/health sin token → E001", metodo="GET", ruta="/health", auth="ninguno"),
        raw_step(None, "/health con token → ok", metodo="GET", ruta="/health"),
        raw_step('{"m":"PING;64"}', "/msg sin token → E001", auth="ninguno"),
        raw_step(None, "HEAD /msg → 404 sin cuerpo", metodo="HEAD"),
    ],
}


def send_original(step, seq):
    hip = f"centinela: {step['hip']} (igual que el perfil v1)"
    req = step["request"]
    if isinstance(req, dict):
        return prober.call(step["metodo"], step["ruta"], req, auth=step["auth"], seq=seq, hipotesis=hip)
    return prober.call(step["metodo"], step["ruta"], raw=req, auth=step["auth"], seq=seq, hipotesis=hip)


def log_lines():
    p = ROOT / "experimentos.jsonl"
    return sum(1 for _ in p.open(encoding="utf-8")) if p.exists() else 0


def vuelta():
    replica = InProcess()
    seq = "centinela-" + datetime.now().strftime("%H%M")
    diffs, n = [], 0
    for nombre, pasos in CASOS.items():
        prober.reset(seq, f"centinela: estado limpio para el caso '{nombre}'")
        replica.reset()
        for st in pasos:
            e = send_original(st, seq)
            n += 1
            if e.get("infra"):
                continue   # rate limit de la infraestructura, no del servicio
            status, body = replica.send(st)
            if not (status == e["status"] and same(body, e["response"])):
                diffs.append({"id": e["id"], "caso": nombre, "hip": st["hip"],
                              "request": st["request"] if not isinstance(st["request"], str) or len(st["request"]) < 80 else "(cuerpo grande)",
                              "original": [e["status"], e["response"]], "reemplazo": [status, body]})
    return seq, n, diffs


def write_status(history):
    last = history[-1]
    estado = "🔴 **CAMBIO DETECTADO**" if last["diffs"] else "🟢 Sin cambios"
    lines = [
        "---", "tags: [ejecucion, incidente, centinela]", "---",
        "# Centinela del original", "",
        f"> [!{'warning' if last['diffs'] else 'tip'}] Estado: {estado} · última vuelta {last['hora']} · "
        f"{last['n']} requests · `python bench/sentinel.py`",
        "", "Compara cada respuesta del original con el reemplazo (perfil v1). Una diferencia = el original cambió. "
        "Respuesta: [[Incidente]] → spec §6 → perfil `v2`.", "",
        "| Hora | Seq | Requests | Diferencias |", "|---|---|---|---|",
    ]
    lines += [f"| {h['hora']} | `{h['seq']}` | {h['n']} | {'**' + str(len(h['diffs'])) + '**' if h['diffs'] else 0} |"
              for h in reversed(history[-40:])]
    first = next((h for h in history if h["diffs"]), None)
    if first:
        lines += ["", f"## Diferencias (primera detección: {first['hora']})", "",
                  "| Log id | Caso | Qué se probaba | Request | Original | Reemplazo |", "|---|---|---|---|---|---|"]
        for d in last["diffs"] or first["diffs"]:
            lines.append(f"| {d['id']} | {d['caso']} | {d['hip']} | `{json.dumps(d['request'], ensure_ascii=False)}` | "
                         f"`{d['original'][0]} {json.dumps(d['original'][1], ensure_ascii=False)}` | "
                         f"`{d['reemplazo'][0]} {json.dumps(d['reemplazo'][1], ensure_ascii=False)}` |")
    STATUS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--every", type=float, default=10, help="minutos entre vueltas")
    a = ap.parse_args()
    history = []
    while True:
        if log_lines() >= DAILY_BUDGET_STOP:
            print("Presupuesto diario casi agotado: el centinela se detiene.", flush=True)
            return
        try:
            seq, n, diffs = vuelta()
        except Exception as e:   # red caída, etc.: reintenta en la próxima vuelta
            print(f"[{datetime.now():%H:%M}] error en la vuelta: {e}", flush=True)
            seq, n, diffs = None, 0, None
        if seq:
            history.append({"hora": datetime.now().strftime("%H:%M"), "seq": seq, "n": n, "diffs": diffs})
            write_status(history)
            if diffs:
                print(f"\a[{history[-1]['hora']}] 🔴 CAMBIO DETECTADO en {len(diffs)} respuestas ({seq}):", flush=True)
                for d in diffs:
                    print(f"   #{d['id']} {d['hip']}: original {d['original']} ≠ reemplazo {d['reemplazo']}", flush=True)
            else:
                print(f"[{history[-1]['hora']}] 🟢 sin cambios ({n} requests, {seq})", flush=True)
        if a.once or datetime.now().strftime("%H:%M") >= FIN:
            return
        time.sleep(a.every * 60)


if __name__ == "__main__":
    main()
