"""Tester diferencial: reproduce lo grabado del original contra el reemplazo con el comparador del jurado.

Un caso = un POST /__reset + los requests que le siguen dentro de la misma secuencia del log.
Fuentes: material/pruebas/ejemplos.jsonl (un caso) + experimentos.jsonl.

Uso:
    python bench/diff.py                       # en proceso (importa app/, sin servidor)
    python bench/diff.py --target URL          # contra un despliegue (usa TEAM_TOKEN de .env)
    python bench/diff.py --split holdout       # solo casos hold-out (hash de la seq)
    python bench/diff.py -v                    # muestra cada diferencia
    python bench/diff.py --seq s17-anula       # solo una secuencia (repetible)
    python bench/diff.py --profile v1          # fuerza un perfil para todos los casos (por defecto: auto)

Versiones (incidente, spec §6): el original pasó de v1 a v2 entre las 15:50 y las 15:55. Con --profile auto
cada caso se compara con el perfil de la versión con que se grabó: id de log ≤ CORTE_V2 (y los 20 ejemplos de la
mañana) → v1; id > CORTE_V2 (regresión `v2-*`, exp26+ y centinela posterior) → v2. --target usa el perfil
desplegado en el destino, así que contra un despliegue solo tiene sentido la era que ese perfil reproduce.
"""
import argparse
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def same(a, b):
    """Comparador del jurado: JSON con claves en cualquier orden; arrays, strings y números idénticos."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def cases():
    out = []
    ej = ROOT / "material" / "pruebas" / "ejemplos.jsonl"
    if ej.exists():
        steps = [{"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": r["request"],
                  "status": r["status"], "response": r["response"], "id": f"ej{r['id']}"}
                 for r in map(json.loads, ej.read_text(encoding="utf-8").splitlines()) if True]
        out.append(("ejemplos", steps))
    log = ROOT / "experimentos.jsonl"
    if log.exists():
        by_seq = defaultdict(list)
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("infra"):
                    continue   # respuesta de la infraestructura (rate limit), no del servicio
                by_seq[r["seq"]].append(r)
        for seq, rows in by_seq.items():
            cur = None
            for r in rows:
                if r.get("ruta") == "/__reset" and r.get("auth") == "propio" and r.get("status") == 200:
                    if cur:
                        out.append((seq, cur))
                    cur = []
                elif cur is not None:
                    cur.append(r)
            if cur:
                out.append((seq, cur))
    return out


CORTE_V2 = 3164   # último id de log grabado con v1 (centinela-1550); desde el 3165 todo es v2 (regresión v2-*)


def era(case):
    """'v1' o 'v2' según el id de log del primer paso del caso (los ejemplos 'ejN' son de la mañana → v1)."""
    first = case[0]["id"] if case else None
    return "v2" if isinstance(first, int) and first > CORTE_V2 else "v1"


def split_of(seq):
    return "holdout" if int(hashlib.sha1(seq.encode()).hexdigest(), 16) % 5 == 0 else "dev"


class InProcess:
    def __init__(self):
        os.environ["TEAM_TOKEN"] = "token-de-prueba"
        from app import main
        self.main = main
        self.token = "token-de-prueba"

    def reset(self):
        self.main.STORE.reset(self.token)

    def send(self, step, perfil=None):
        headers = {b"host": b"localhost"}
        auth = {"propio": f"Bearer {self.token}", "invalido": "Bearer x", "ninguno": None}.get(step.get("auth"), None)
        if auth:
            headers[b"authorization"] = auth.encode()
        req = step.get("request")
        raw = json.dumps(req, ensure_ascii=False).encode() if isinstance(req, (dict, list)) else (req or "").encode()
        status, body = self.main.handle(step["metodo"], step["ruta"], headers, raw, perfil)
        return (status, "") if step["metodo"] == "HEAD" else (status, body)   # el adaptador ASGI vacía el cuerpo en HEAD


def _no_enviado(err):
    """True solo si el request no llegó a salir (DNS o conexión rechazada): reintentarlo es seguro.
    Un timeout o un corte a mitad pueden ocurrir después de que el servidor procesó un POST
    (ALTA, DEPOSITO, TRANSFER…): reenviarlo lo ejecutaría dos veces."""
    reason = getattr(err, "reason", err)
    return isinstance(reason, (socket.gaierror, ConnectionRefusedError))


class Remote:
    def __init__(self, url):
        load_env()
        self.url, self.token = url.rstrip("/"), os.environ["TEAM_TOKEN"]

    def _call(self, method, path, raw, auth):
        h = {"Content-Type": "application/json"}
        if auth:
            h["Authorization"] = auth
        req = urllib.request.Request(self.url + path, data=raw if method != "GET" else None, method=method, headers=h)
        for attempt in range(5):   # la red local tiene cortes de DNS intermitentes
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    status, text = r.status, r.read().decode()
                break
            except urllib.error.HTTPError as e:
                status, text = e.code, e.read().decode()
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt == 4 or not _no_enviado(e):
                    raise
                time.sleep(1 + attempt)
        try:
            return status, json.loads(text)
        except ValueError:
            return status, text

    def reset(self):
        self._call("POST", "/__reset", b"", f"Bearer {self.token}")

    def send(self, step, perfil=None):   # el perfil lo decide el despliegue (BEHAVIOR_PROFILE)
        auth = {"propio": f"Bearer {self.token}", "invalido": "Bearer x", "ninguno": None}.get(step.get("auth"), None)
        req = step.get("request")
        raw = json.dumps(req, ensure_ascii=False).encode() if isinstance(req, (dict, list)) else (req or "").encode()
        return self._call(step["metodo"], step["ruta"], raw, auth)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target")
    ap.add_argument("--split", choices=["dev", "holdout", "all"], default="all")
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--seq", action="append", help="solo estas secuencias (repetible)")
    ap.add_argument("--profile", choices=["auto", "v1", "v2"], default="auto",
                    help="perfil del reemplazo en proceso: auto = por era del caso (CORTE_V2)")
    ap.add_argument("--era", choices=["v1", "v2", "all"], default="all", help="solo casos grabados en esa versión")
    a = ap.parse_args()
    tgt = Remote(a.target) if a.target else InProcess()
    from app.profiles import PERFILES
    total = ok_cases = steps = ok_steps = ok_status = 0
    por_era = defaultdict(lambda: [0, 0])
    fails = defaultdict(int)
    todos = cases()
    if a.seq:
        # Una secuencia pedida que no existe, o que no empieza con /__reset (no hay caso que reproducir),
        # no puede dar "0/0" con éxito: se informa y se sale con error.
        con_caso = {seq for seq, _ in todos}
        faltan = [s for s in a.seq if s not in con_caso]
        if faltan:
            print(f"Secuencias sin casos reproducibles (no existen o no empiezan con /__reset): {', '.join(faltan)}")
            sys.exit(2)
    for seq, case in todos:
        e = era(case)
        if a.era != "all" and e != a.era:
            continue
        perfil = PERFILES[e if a.profile == "auto" else a.profile]
        if a.split != "all" and split_of(seq) != a.split:
            continue
        if a.seq and seq not in a.seq:
            continue
        tgt.reset()
        total += 1
        case_ok = True
        for st in case:
            status, body = tgt.send(st, perfil)
            steps += 1
            good = status == st["status"] and same(body, st["response"])
            ok_steps += good
            ok_status += status == st["status"]
            if not good:
                case_ok = False
                key = st["response"].get("error") if isinstance(st["response"], dict) else str(st["status"])
                fails[key or "ok"] += 1
                if a.v:
                    print(f"  ✗ [{seq}|{perfil.nombre}] #{st['id']} {st.get('metodo')} {st.get('ruta')} {json.dumps(st.get('request'), ensure_ascii=False)}\n"
                          f"      esperado {st['status']} {json.dumps(st['response'], ensure_ascii=False)}\n"
                          f"      obtenido {status} {json.dumps(body, ensure_ascii=False)}")
        ok_cases += case_ok
        por_era[e][0] += case_ok
        por_era[e][1] += 1
    pct = lambda x, n: f"{100 * x / n:.1f}%" if n else "—"
    print(f"Casos {ok_cases}/{total} ({pct(ok_cases, total)}) · pasos {ok_steps}/{steps} ({pct(ok_steps, steps)}) · "
          f"status {pct(ok_status, steps)} · split={a.split} · profile={a.profile}")
    for e, (ok_e, n_e) in sorted(por_era.items()):
        print(f"  era {e} (log {'≤' if e == 'v1' else '>'} {CORTE_V2}): casos {ok_e}/{n_e} ({pct(ok_e, n_e)})")
    if fails:
        print("Fallos por respuesta esperada:", dict(sorted(fails.items(), key=lambda kv: -kv[1])))
    if total == 0:
        print("Ningún caso coincidió con los filtros: no hay nada verificado.")
        sys.exit(2)
    sys.exit(0 if ok_cases == total else 1)


if __name__ == "__main__":
    main()
