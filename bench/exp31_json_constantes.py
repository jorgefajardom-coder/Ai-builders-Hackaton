"""Exp 31 — ¿El original rechaza las constantes no JSON NaN / Infinity / -Infinity? (reportado por el equipo, 16:30)

Se mandan bytes crudos. Hipótesis: el original parsea con semántica de JSON.parse (como las claves duplicadas,
EN-11), que no acepta esas constantes → 400 E100, igual que cualquier JSON inválido.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from prober import call, show  # noqa: E402

S = "s31-json-constantes"
for raw, hip in [
    ('{"m":"PING;64","x":NaN}', "NaN en una clave extra ignorada: ¿E100 (JSON.parse) o pong (parser permisivo)?"),
    ('{"m":NaN}', "m = NaN: ¿E100 (no es JSON) o E102 (falta m)?"),
    ('{"m":Infinity}', "m = Infinity: ¿E100?"),
    ('{"m":-Infinity}', "m = -Infinity: ¿E100? (sin prueba previa)"),
    ('{"m":"PING;64","x":"NaN"}', "control: el string \"NaN\" es JSON válido → pong"),
]:
    show(call("POST", "/msg", raw=raw, headers={"Content-Type": "application/json"}, seq=S, hipotesis=hip))
