"""Pipeline de validación de /msg con orden declarado por el perfil (ADR-009). Gana el primer error.

Orden observado (docs/01 Problema/Hallazgos exploración.md, tabla de precedencia):
tamaño E101 → JSON E100 → campo m E102 → separador E103 → segmentos vacíos E104 → PING (solo aridad)
→ formato de control E201 → valor de control E202 → comando E301 → aridad E302 → [comando: E303, E304,
existencia E401/E402, negocio E506/E507]. Ruta (E404) y auth (E001) se resuelven antes, en el adaptador.
"""
import json
import re
import sys

from .checkval import control
from .commands import REGISTRO
from .errors import DomainError

MAX_BODY = 8192                       # 8193 bytes → E101 (log 1384)
# json.loads usa la pila de recursión de Python (límite 1000): un cuerpo de 8 KB admite hasta ~4096 niveles
# de anidamiento, que JSON.parse del original acepta. Margen holgado sobre la pila ya usada.
_PARSE_RECURSION = 10_000
CONTROL_RE = re.compile(r"[0-9]{1,2}")  # solo ASCII; '014', '+14', '１４' → E201 (exp06)


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sugerencia(nombre: str):
    """Comando más cercano a distancia ≤ 2; empate → el primero alfabético (ALTA gana: log 1576)."""
    best, best_d = None, 3
    for cmd in sorted(REGISTRO):
        d = levenshtein(nombre.upper(), cmd)
        if d < best_d:
            best, best_d = cmd, d
    return best


def etapa_tamano(ctx):
    if len(ctx["raw"]) > MAX_BODY:
        raise DomainError("E101")


def etapa_json(ctx):
    limite = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limite, _PARSE_RECURSION))
    try:
        ctx["data"] = json.loads(ctx["raw"].decode("utf-8"))   # clave duplicada: gana la última (como el original)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise DomainError("E100")
    finally:
        sys.setrecursionlimit(limite)


def etapa_campo_m(ctx):
    data = ctx["data"]
    if not isinstance(data, dict) or not isinstance(data.get("m"), str):
        raise DomainError("E102")
    ctx["m"] = data["m"]


def etapa_separador(ctx):
    if ";" not in ctx["m"]:
        raise DomainError("E103")
    ctx["segmentos"] = ctx["m"].split(";")


def etapa_segmentos(ctx):
    if any(s == "" for s in ctx["segmentos"]):       # " " no cuenta como vacío
        raise DomainError("E104")


def etapa_ping(ctx):
    """PING no valida el control (PING;XX → pong), pero sí la aridad (PING;X;XX → E302)."""
    nombre, *args = ctx["segmentos"][:-1]
    if nombre.upper() == "PING":
        if args:
            raise DomainError("E302")
        ctx["resultado"] = REGISTRO["PING"].handler(None, [], None)


def etapa_control_formato(ctx):
    if not CONTROL_RE.fullmatch(ctx["segmentos"][-1]):
        raise DomainError("E201")


def etapa_control_valor(ctx):
    cuerpo = ";".join(ctx["segmentos"][:-1])
    if ctx["segmentos"][-1] != str(control(cuerpo)):   # sin ceros a la izquierda: '08' ≠ '8' → E202
        raise DomainError("E202")


def etapa_comando(ctx):
    nombre = ctx["segmentos"][0]
    cmd = REGISTRO.get(nombre.upper())               # sin recortar: "PING " → E301
    if cmd is None:
        s = sugerencia(nombre)
        raise DomainError("E301", {"sugerencia": s} if s else None)
    ctx["cmd"] = cmd


def etapa_aridad(ctx):
    args = ctx["segmentos"][1:-1]
    if len(args) != ctx["cmd"].aridad:
        raise DomainError("E302")
    ctx["args"] = args


ETAPAS = {
    "tamano": etapa_tamano, "json": etapa_json, "campo_m": etapa_campo_m, "separador": etapa_separador,
    "segmentos": etapa_segmentos, "ping": etapa_ping, "control_formato": etapa_control_formato,
    "control_valor": etapa_control_valor, "comando": etapa_comando, "aridad": etapa_aridad,
}


def procesar_msg(raw: bytes, estado, perfil):
    ctx = {"raw": raw}
    for nombre in perfil.orden_msg:
        ETAPAS[nombre](ctx)
        if "resultado" in ctx:                       # cortocircuito (PING)
            return ctx["resultado"]
    return ctx["cmd"].handler(estado, ctx["args"], perfil)
