"""Exp 21 — ¿Existen los comandos HALT y NOTAS? (dato reportado por otro equipo, sin evidencia propia).

Con control válido: comando desconocido → E301; comando conocido con aridad distinta → E302.
Se prueba cada candidato con 0..3 argumentos, en mayúsculas y minúsculas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402

S = "s21-halt-notas"
reset(S)
for cmd in ["HALT", "NOTAS", "halt", "Notas"]:
    for args in ([], ["AC-0001"], ["AC-0001", "hola"], ["AC-0001", "hola", "x"]):
        body = ";".join([cmd, *args])
        e = msg(f"{body};{control(body)}", S,
                f"¿{cmd} existe? con {len(args)} args: E301 = no existe; E302 = existe con otra aridad; otra respuesta = existe")
        show(e)
