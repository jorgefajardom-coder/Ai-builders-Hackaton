"""Exp 11 — Forma del cuerpo de POST /msg: JSON inválido, sin 'm', 'm' no string, claves extra,
Content-Type distinto, tamaño grande. Esperamos códigos E1xx (familia 'entrada')."""
from control_model import control
from prober import call, msg, reset, show

S = "s11-cuerpo"
reset(S, "estado limpio: forma del cuerpo")

J = {"Content-Type": "application/json"}
CASOS = [
    (dict(raw="esto no es json", headers=J), "cuerpo no JSON con Content-Type json -> error E10x de JSON inválido"),
    (dict(raw="", headers=J), "cuerpo vacío con Content-Type json"),
    (dict(raw=None), "sin cuerpo y sin Content-Type"),
    (dict(body={}), "objeto sin 'm' -> E10x falta m"),
    (dict(body={"M": "PING;64"}), "clave 'M' mayúscula: ¿se trata como ausente?"),
    (dict(body={"m": 123}), "'m' numérico -> E10x tipo"),
    (dict(body={"m": None}), "'m' null"),
    (dict(body={"m": ["PING;64"]}), "'m' array"),
    (dict(body={"m": "PING;64", "x": 1}), "clave extra: ¿se ignora -> pong?"),
    (dict(raw='["PING;64"]', headers=J), "cuerpo JSON array en lugar de objeto"),
    (dict(raw='"PING;64"', headers=J), "cuerpo JSON string"),
    (dict(raw='null', headers=J), "cuerpo JSON null"),
    (dict(raw='{"m":"PING;64"}', headers={"Content-Type": "text/plain"}), "JSON válido con Content-Type text/plain: ¿se parsea igual?"),
    (dict(raw='{"m":"PING;64"}'), "JSON válido sin Content-Type"),
    (dict(raw='{"m":"PING;64","m":"PING;XX"}', headers=J), "clave 'm' duplicada: gana la última (JSON.parse) -> pong igualmente"),
    (dict(raw='{"m":"PING;64"} basura', headers=J), "JSON seguido de basura -> inválido"),
]
for kw, h in CASOS:
    show(call("POST", "/msg", seq=S, hipotesis=h, **kw))

# Los casos de tamaño se movieron a exp12_tamano.py
