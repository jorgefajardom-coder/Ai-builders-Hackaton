"""Exp 30 — Incidente v2: barrido diferencial de requests de UN paso (sin estado previo) contra el perfil v2.

Motivo: confirmar que ninguna diferencia de v2 vive fuera de los 3 cambios conocidos (CB-04..06), que no
pueden afectar a un request sin estado previo. Se manda tras /__reset un abanico amplio de mensajes sin estado
(los que mutan estado —ALTA— van al final) y cada respuesta se compara con el reemplazo en proceso (perfil v2),
que sigue la misma secuencia. Cada línea del log queda con la conclusión verificada (igual / REFUTADA).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import prober  # noqa: E402
from app.checkval import control  # noqa: E402
from app.profiles import PERFILES  # noqa: E402
from diff import InProcess, same  # noqa: E402

V2 = PERFILES["v2"]


def ok(body):
    return f"{body};{control(body)}"


M = []          # (m, qué se prueba)
def add(m, hip):
    M.append(({"m": m}, hip))


# PING y variantes
for m in ["PING;64", "ping;1", "PING; ", "PING;XX;", "PING;;", "Ping;64;64", "PING;0", "PING;100", "PING;-1",
          "PING;😀", " PING;64", "PING ;64", "PONG;" + str(control("PONG")), "PIN;" + str(control("PIN"))]:
    add(m, "v2 un paso: variante de PING")
# comandos sin estado / con cuenta u operación inexistente
for body in ["CONSULTA;AC-0001", "CONSULTA;AC-0000", "CONSULTA;ac-0001", "CONSULTA;X", "ANULA;OP-0001", "ANULA;OP-0000",
             "ANULA;AC-0001", "ANULA;x", "NOTAS", "notas", "HALT;x", "HALT;AC-0001", "HALT;0", "HALT;01", "HALT;SI",
             "NOTAS;x", "HALT", "HALT;x;y", "CONSULTA", "ANULA", "DEPOSITO;AC-0001", "TRANSFER;AC-0001;AC-0002"]:
    add(ok(body), f"v2 un paso: {body} sin estado")
for monto in ["0", "1", "49999", "50000", "50001", "99999", "100000", "100001", "9999999999", "10000000000",
              "-1", "1.5", "007", "abc", "1e3", " 1"]:
    add(ok(f"DEPOSITO;AC-0001;{monto}"), f"v2 un paso: DEPOSITO a cuenta inexistente con monto {monto!r}")
    add(ok(f"TRANSFER;AC-0001;AC-0002;{monto}"), f"v2 un paso: TRANSFER entre cuentas inexistentes con monto {monto!r}")
for monto in ["50001", "100001", "0", "5"]:
    add(ok(f"TRANSFER;AC-0001;AC-0001;{monto}"), f"v2 un paso: TRANSFER origen=destino inexistente, monto {monto}")
# control y comando
for body in ["CONSULTA;AC-0001", "ALTA;Ana", "NOTAS"]:
    c = control(body)
    for bad in [str(c % 97 + 1), f"0{c}" if c < 10 else f"{c}0", "XX", "1.0", "-" + str(c)]:
        add(f"{body};{bad}", f"v2 un paso: control '{bad}' para {body} (correcto {c})")
for cmd in ["CONSULT", "DEPOSIT", "TRANSFE", "ANULAR", "NOTA", "HALTT", "ALT", "ALTAS", "XYZ", "BORRAR", "SALDO",
            "RETIRO", "LISTA", "consultar", "Transfers", "DEPOSITOS", "ALTA😀", "AL😀", "ÁLTA", "PINGG", "STATUS",
            "VERSION", "HELP", "AYUDA", "CIERRE", "EXPORT"]:
    add(ok(f"{cmd};x"), f"v2 un paso: comando desconocido '{cmd}' (E301 y sugerencia)")
    add(ok(cmd), f"v2 un paso: comando '{cmd}' sin argumentos")
# forma del mensaje
for m in ["", "PING", "CONSULTA;;14", ";", ";;", "CONSULTA;AC-0001;", ";14", "a;b;c;d;e;f;g;h", "ALTA;Ana;5;5",
          "CONSULTA;AC-0001;14;", "CONSULTA;AC-0001;14 ", "CONSULTA;AC-0001;１４"]:
    add(m, f"v2 un paso: forma del mensaje {m!r}")
# cuerpos no estándar (JSON válido)
RAWS = [(None, "{}"), (None, "[]"), (None, "null"), (None, '"PING;64"'), (None, "123"), (None, '{"m": 5}'),
        (None, '{"m": null}'), (None, '{"m": ["PING;64"]}'), (None, '{"M": "PING;64"}'), (None, ""),
        (None, "no json"), (None, '{"m": "PING;64", "m": "PING;XX"}'), (None, '  {"m":"PING;64"}  '),
        (None, '{"m":"\\u0050ING;64"}'), (None, '{"m": "PING;64"} x')]
# rutas, métodos, auth
RUTAS = [("GET", "/msg", "propio"), ("PUT", "/msg", "propio"), ("DELETE", "/msg", "propio"), ("POST", "/health", "propio"),
         ("GET", "/__reset", "propio"), ("POST", "/msg/", "propio"), ("POST", "/MSG", "propio"), ("GET", "/", "propio"),
         ("POST", "/internal/export-docs", "ninguno"), ("GET", "/health", "invalido"), ("POST", "/__reset", "ninguno"),
         ("POST", "/msg", "ninguno"), ("POST", "/msg", "invalido"), ("GET", "/nada", "ninguno")]
# los que crean estado, al final
ALTAS = ["ALTA;Ana", "ALTA; ", "ALTA;José Ñandú", "ALTA;李小龙", "ALTA;😀", "ALTA;O'Brien", "ALTA;12345", "ALTA;a b c",
         "alta;Ana", "ALTA;" + "x" * 300]


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    seq = "s30-un-paso-v2"
    rep = InProcess()
    prober.reset(seq, "estado limpio: todos los requests siguientes son 'primer request' salvo ALTA (al final)")
    rep.reset()
    pasos = [{"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": b, "hip": h} for b, h in M]
    pasos += [{"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": r, "hip": f"v2 un paso: cuerpo crudo {r!r}"}
              for _, r in RAWS]
    pasos += [{"metodo": me, "ruta": ru, "auth": au, "request": None, "hip": f"v2 un paso: {me} {ru} auth={au}"}
              for me, ru, au in RUTAS]
    pasos += [{"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": {"m": ok(a)}, "hip": f"v2: {a[:30]} (crea estado)"}
              for a in ALTAS]
    pasos += [{"metodo": "POST", "ruta": "/msg", "auth": "propio", "request": {"m": ok("CONSULTA;AC-0001")},
               "hip": "v2: CONSULTA de la cuenta recién creada → \"0.00\""}]
    diffs = 0
    for st in pasos:
        req = st["request"]
        if isinstance(req, dict):
            e = prober.call(st["metodo"], st["ruta"], req, auth=st["auth"], seq=seq, hipotesis=st["hip"], log=False)
        else:
            e = prober.call(st["metodo"], st["ruta"], raw=req, auth=st["auth"], seq=seq, hipotesis=st["hip"], log=False)
        status, body = rep.send(st, V2)
        igual = status == e["status"] and same(body, e["response"])
        e["conclusion"] = ("confirmada: igual que el perfil v2" if igual else
                           f"REFUTADA: el perfil v2 responde {status} {json.dumps(body, ensure_ascii=False)}")
        prober.append(e)
        if not igual:
            diffs += 1
            print(f"✗ #{e['id']} {st['metodo']} {st['ruta']} {json.dumps(req, ensure_ascii=False)[:120]}\n"
                  f"    original {e['status']} {json.dumps(e['response'], ensure_ascii=False)[:200]}\n"
                  f"    v2       {status} {json.dumps(body, ensure_ascii=False)[:200]}")
    print(f"{len(pasos)} requests · {diffs} diferencias")


if __name__ == "__main__":
    main()
