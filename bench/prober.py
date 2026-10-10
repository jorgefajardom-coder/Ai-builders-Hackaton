"""Cliente del servicio original que registra cada request en experimentos.jsonl.

Toda llamada al original pasa por aquí: así el log de experimentos se escribe solo
y nunca contiene credenciales (solo una etiqueta de qué auth se usó).
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "experimentos.jsonl"
MIN_INTERVAL = 0.12  # 10 req/s por token


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
BASE = os.environ["CAJA_URL"].rstrip("/")
TOKEN = os.environ["CAJA_TOKEN"]
_last = 0.0


def _next_id():
    if not LOG.exists():
        return 1
    n = 0
    with LOG.open(encoding="utf-8") as f:
        for _ in f:
            n += 1
    return n + 1


def _auth_header(auth):
    """auth: 'propio' | 'ninguno' | 'invalido' | cualquier otro string literal (se registra tal cual)."""
    if auth == "propio":
        return f"Bearer {TOKEN}"
    if auth == "ninguno":
        return None
    if auth == "invalido":
        return "Bearer cn-p-token-invalido"
    return auth


def call(method, path, body=None, *, raw=None, auth="propio", headers=None,
         seq, hipotesis, conclusion=None, log=True):
    """Manda un request al original y lo registra. `body` es un dict JSON; `raw` es texto crudo."""
    global _last
    wait = MIN_INTERVAL - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)

    data = None
    hdrs = {"User-Agent": "caja-negra-bench"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw.encode("utf-8") if isinstance(raw, str) else raw
    if headers:
        hdrs.update(headers)
    a = _auth_header(auth)
    if a is not None:
        hdrs["Authorization"] = a

    req = urllib.request.Request(BASE + path, data=data, method=method, headers=hdrs)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                status, rh, text = r.status, r.headers, r.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            status, rh, text = e.code, e.headers, e.read().decode("utf-8", "replace")
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 3:
                raise
            time.sleep(1 + attempt)
    _last = time.monotonic()

    try:
        response = json.loads(text)
    except ValueError:
        response = text
    x_req = rh.get("X-Req")
    try:
        x_req = int(x_req)
    except (TypeError, ValueError):
        pass

    entry = {
        "id": None,
        "seq": seq,
        "x_req": x_req,
        "hipotesis": hipotesis,
        "request": body if body is not None else raw,
        "status": status,
        "response": response,
        "conclusion": conclusion,
        # Campos extra (no exigidos por el formato) para reproducir el request exacto.
        "metodo": method,
        "ruta": path,
        "auth": auth if auth in ("propio", "ninguno", "invalido") else "literal",
        "content_type": rh.get("Content-Type"),
    }
    if rh.get("X-Frontier-Infra"):
        entry["infra"] = rh.get("X-Frontier-Infra")
    if log:
        entry["id"] = _next_id()
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def reset(seq, hipotesis="estado limpio antes de la secuencia"):
    return call("POST", "/__reset", seq=seq, hipotesis=hipotesis)


def msg(m, seq, hipotesis, **kw):
    return call("POST", "/msg", {"m": m}, seq=seq, hipotesis=hipotesis, **kw)


def show(e):
    print(f"#{e['id']} [{e['seq']}] {e['metodo']} {e['ruta']} {json.dumps(e['request'], ensure_ascii=False)}"
          f" -> {e['status']} {json.dumps(e['response'], ensure_ascii=False)}"
          f"  x_req={e['x_req']} ct={e['content_type']}{' INFRA=' + e['infra'] if 'infra' in e else ''}")
