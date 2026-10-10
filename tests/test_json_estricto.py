"""Regresiones LOCALES: el parser de /msg rechaza las constantes no JSON NaN, Infinity y -Infinity (400 E100).

Se envían bytes crudos (sin serializar), para que nada filtre las constantes antes del reemplazo.
No llama al original ni al deploy.

Uso:
    python tests/test_json_estricto.py                         # en proceso
    python tests/test_json_estricto.py --http http://127.0.0.1:8099   # contra un uvicorn LOCAL (1 worker)
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

E100 = (400, {"error": "E100", "mensaje": "json inválido"})
E102 = (400, {"error": "E102", "mensaje": "falta m"})
PONG = (200, {"pong": True})

CASOS = [
    (b'{"m":"PING;64","x":NaN}', E100, "NaN en clave extra ignorada"),
    (b'{"m":"PING;64","x":Infinity}', E100, "Infinity en clave extra"),
    (b'{"m":"PING;64","x":-Infinity}', E100, "-Infinity en clave extra"),
    (b'{"m":NaN}', E100, "m = NaN (antes daba E102)"),
    (b'{"m":Infinity}', E100, "m = Infinity"),
    (b'{"m":-Infinity}', E100, "m = -Infinity"),
    (b"NaN", E100, "NaN como cuerpo raíz"),
    (b"Infinity", E100, "Infinity como cuerpo raíz"),
    (b"-Infinity", E100, "-Infinity como cuerpo raíz"),
    (b'{"m":"PING;64","x":"NaN"}', PONG, "string \"NaN\" no es una constante"),
    (b'{"m":"PING;64","x":null}', PONG, "null es JSON válido"),
    (b'{"m":123}', E102, "m numérico sigue dando E102"),
    (b'{"m":"PING;64",}', E100, "coma final"),
    (b"{'m':'PING;64'}", E100, "comillas simples"),
    (b'{"m":"PING;64"', E100, "objeto sin cerrar"),
    (b"esto no es json", E100, "texto plano"),
    (b'{"m":"PING;1","m":"PING;64"}', PONG, "clave duplicada: gana la última (sin cambios)"),
]


def en_proceso():
    os.environ["TEAM_TOKEN"] = "token-local"
    from app import main
    headers = {b"authorization": b"Bearer token-local", b"host": b"localhost"}

    def enviar(raw):
        main.STORE.reset("token-local")
        return main.handle("POST", "/msg", headers, raw)
    return enviar


def por_http(base):
    token = os.environ.get("TEAM_TOKEN_LOCAL", "token-local")

    def enviar(raw):
        req = urllib.request.Request(base.rstrip("/") + "/msg", data=raw, method="POST",
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())
    return enviar


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", help="URL de un uvicorn LOCAL; nunca el deploy")
    a = ap.parse_args()
    if a.http and not a.http.startswith(("http://127.0.0.1", "http://localhost")):
        sys.exit("Solo contra un servidor local: el deploy comparte estado con el portal.")
    enviar = por_http(a.http) if a.http else en_proceso()
    fallos = 0
    for raw, esperado, desc in CASOS:
        obtenido = enviar(raw)
        ok = obtenido == esperado
        fallos += not ok
        print(f"{'✓' if ok else '✗'} {desc}: {raw.decode()} → {obtenido[0]} {json.dumps(obtenido[1], ensure_ascii=False)}"
              + ("" if ok else f"   (esperado {esperado[0]} {json.dumps(esperado[1], ensure_ascii=False)})"))
    print(f"\n{len(CASOS) - fallos}/{len(CASOS)} regresiones OK · modo {'HTTP ' + a.http if a.http else 'en proceso'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
