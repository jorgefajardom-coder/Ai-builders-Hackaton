"""Exp 29 — Incidente v2: comprobación de que "el resto es idéntico a v1" con entradas NO vistas en la mañana.

La regresión (log 3165–3694) repitió el corpus de la mañana; aquí se predicen respuestas nuevas con el
perfil v1 (salvo los 3 cambios): fórmula del control sobre cuerpos nuevos, PING, NOTAS, HALT;x (nunca HALT;1),
sugerencia de E301, rutas y auth.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import call, msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


S = "s29a-sanidad"
reset(S)
for nombre in ("Zoe Quintero", "Ximena-77", "Wilfredo_J"):
    m(f"ALTA;{nombre}", S, f"v2 sin cambio: control predicho {control('ALTA;' + nombre)} para un nombre nuevo → 201")
m("ALTA;Ximena-77".replace("77", "78"), S, "control nuevo (ALTA;Ximena-78) → 201 AC-0004")
show(msg("ALTA;Pablo;" + str(control("ALTA;Pablo") % 97 + 1), S, "v2 sin cambio: control desplazado en 1 → E202"))
show(msg("PING;ZZ", S, "v2 sin cambio: PING no valida el control"))
m("NOTAS", S, "v2 sin cambio: NOTAS estática (misma nota N-01)")
m("HALT;x", S, "v2 sin cambio: HALT;x → 409 E520 (no se envía HALT;1)")
m("CONSULTAS;AC-0001", S, "v2 sin cambio: E301 con sugerencia CONSULTA")
m("TRANSFERIR;AC-0001;AC-0002;5", S, "v2 sin cambio: E301 sin sugerencia (distancia > 2)")
m("DEPOSITO;AC-0001;49999", S, "depósito 49999 en AC-0001")
m("TRANSFER;AC-0001;AC-0002;50000", S, "v2: 50000 (dentro del límite) con saldo 49999 → E507")
m("TRANSFER;AC-0001;AC-0002;49999", S, "v2: transferir todo el saldo → 200")
m("ANULA;OP-0002", S, "v2 sin cambio: ANULA → 200 ok:true")
m("ANULA;OP-0002", S, "v2 sin cambio: ANULA repetida → 200 ok:false 'ya anulada'")
m("CONSULTA;AC-0002", S, "v2: AC-0002 vuelve a 0 → \"0.00\"")
show(call("GET", "/health", seq=S, hipotesis="v2 sin cambio: /health con token → 200 ok"))
show(call("GET", "/health", seq=S, auth="ninguno", hipotesis="v2 sin cambio: /health sin token → 401 E001"))
show(call("POST", "/msg", {"m": "PING;64"}, seq=S, auth="invalido", hipotesis="v2 sin cambio: token inválido → 401 E001"))
show(call("GET", "/v2", seq=S, hipotesis="v2 sin cambio: ruta inexistente (incluida /v2) → 404 E404"))
