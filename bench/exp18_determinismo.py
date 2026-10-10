"""Exp 18 — Determinismo: reproduce los 20 ejemplos dos veces tras reset y compara status+cuerpo.
Después, precedencias sueltas pendientes."""
import json
from pathlib import Path
from control_model import control
from prober import msg, reset, show

ROOT = Path(__file__).resolve().parent.parent
EJ = [json.loads(l) for l in open(ROOT / "material/pruebas/ejemplos.jsonl", encoding="utf-8")]

for run in ("a", "b"):
    S = f"s18-determinismo-{run}"
    reset(S, f"estado limpio: repetición {run} de los 20 ejemplos")
    dif = 0
    for ej in EJ:
        e = msg(ej["request"]["m"], S,
                f"repetición {run} del ejemplo {ej['n']}: si el servicio es determinista y no cambió desde la mañana -> {ej['status']} {json.dumps(ej['response'], ensure_ascii=False)}")
        if e["status"] != ej["status"] or e["response"] != ej["response"]:
            dif += 1
            show(e)
    print(run, "diferencias:", dif)

S = "s18-precedencia"
reset(S, "estado limpio: precedencias sueltas")


def m(body, h):
    e = msg(f"{body};{control(body)}", S, h)
    show(e)
    return e


m("ALTA;Ana", "crear AC-0001")
m("ALTA;Beto", "crear AC-0002")
m("DEPOSITO;AC-0001;abc;X", "aridad mala + monto inválido: E302 antes que E303")
m("ALTA", "ALTA sin argumentos -> E302")
m("CONSULTA;AC-0001;AC-0002", "CONSULTA con 2 argumentos -> E302")
m("DEPOSITO;AC-0002;300", "AC-0002 recibe 300 -> OP-0001")
m("TRANSFER;AC-0002;AC-0001;300", "AC-0002 gasta los 300 -> OP-0002")
m("ANULA;OP-0001", "anular un depósito ya gastado: ¿ok y saldo negativo (-300)?")
m("CONSULTA;AC-0002", "saldo de AC-0002: -300 si ANULA no comprueba saldo")
m("TRANSFER;AC-0002;AC-0001;1", "origen con saldo negativo -> E507")
msg("Ping;XX", S, "PING en mayúsculas/minúsculas mezcladas sin control numérico -> pong")
