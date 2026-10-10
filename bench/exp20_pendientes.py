"""Exp 20 — Pendientes: clave 'm' duplicada (¿gana la última?) y métodos OPTIONS/HEAD sobre /msg."""
from prober import call, reset, show

S = "s20-pendientes"
reset(S, "estado limpio: pendientes de entrada")
J = {"Content-Type": "application/json"}
show(call("POST", "/msg", seq=S, headers=J,
          raw='{"m":"CONSULTA;AC-0001;15","m":"CONSULTA;AC-0001;14"}',
          hipotesis="clave m duplicada: si gana la última (JSON.parse) el control 14 es válido -> E401; si gana la primera -> E202"))
show(call("OPTIONS", "/msg", seq=S, hipotesis="OPTIONS /msg: como otros métodos no soportados -> 404 E404 (o 204 si hay CORS)"))
show(call("HEAD", "/msg", seq=S, hipotesis="HEAD /msg: método no soportado -> 404 sin cuerpo"))
