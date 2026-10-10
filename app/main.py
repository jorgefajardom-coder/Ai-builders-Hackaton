"""Adaptador HTTP: catch-all ASGI puro, sin framework (ADR-001). Nunca llama al original.

Orden observado: ruta → auth → manejador (log 12: ruta inexistente sin token da 404, no 401).
Arranque: uvicorn app.main:app --workers 1 --no-server-header
"""
import json
import logging
import time

from . import config
from .errors import DomainError
from .pipeline import procesar_msg
from .profiles import cargar
from .store import InMemoryStore

log = logging.getLogger("caja")
PERFIL = cargar(config.BEHAVIOR_PROFILE)
STORE = InMemoryStore()


def _error(code, extra=None):
    spec = PERFIL.catalogo[code]
    return spec.status, {"error": code, "mensaje": spec.mensaje, **(extra or {})}


def _token(headers):
    auth = headers.get(b"authorization", b"").decode("latin-1")
    if auth.startswith("Bearer ") and config.TEAM_TOKEN and auth[7:] == config.TEAM_TOKEN:
        return auth[7:]
    return None


def handle(method, path, headers, raw):
    destino = PERFIL.rutas.get((method, path))
    if destino is None:
        return _error("E404")
    token = _token(headers)
    if token is None:
        host = headers.get(b"host", b"").decode("latin-1").split(":")[0].lower()
        if destino == "health" and host in config.HEALTHCHECK_HOSTS:   # ADR-004
            return 200, {"ok": True}
        return _error("E001")
    if destino == "health":
        return 200, {"ok": True}
    if destino == "reset":
        STORE.reset(token)
        return 200, {"ok": True}
    try:
        return procesar_msg(raw, STORE.get(token), PERFIL.orden_msg)
    except DomainError as e:
        return _error(e.code, e.extra)


async def _read_body(receive):
    chunks = []
    while True:
        msg = await receive()
        chunks.append(msg.get("body", b""))
        if not msg.get("more_body"):
            return b"".join(chunks)


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    if scope["type"] != "http":
        return
    t0 = time.perf_counter()
    headers = {k.lower(): v for k, v in scope["headers"]}
    raw = await _read_body(receive)
    try:
        status, body = handle(scope["method"], scope["path"], headers, raw)
    except Exception:  # nunca el 500 en texto plano de uvicorn (ADR-001). SUPUESTO: forma del 500.
        log.exception("error no controlado")
        status, body = 500, {"error": "E500", "mensaje": "error interno"}
    # HEAD: mismo status, cuerpo vacío (log 1580).
    payload = b"" if scope["method"] == "HEAD" else json.dumps(body, ensure_ascii=False).encode("utf-8")
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json; charset=utf-8"),
                            (b"content-length", str(len(payload)).encode())]})
    await send({"type": "http.response.body", "body": payload})
    log.info(json.dumps({"m": scope["method"], "p": scope["path"], "s": status,
                         "ms": round((time.perf_counter() - t0) * 1000, 1), "perfil": PERFIL.nombre}))
