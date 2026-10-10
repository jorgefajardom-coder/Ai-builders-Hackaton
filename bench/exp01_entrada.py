"""Exp 01 — Superficie de entrada: health, reset, auth, rutas y métodos."""
from prober import call, msg, reset, show

S = "s1-entrada"
for e in [
    call("GET", "/health", seq=S, hipotesis="GET /health con token propio responde 200"),
    call("GET", "/health", auth="ninguno", seq=S, hipotesis="GET /health sin token: ¿requiere auth?"),
    reset(S),
    msg("PING;64", S, "PING válido responde pong (ejemplo #1)"),
    msg("PING;64", S, "sin token: ¿qué error de auth devuelve /msg?", auth="ninguno"),
    msg("PING;64", S, "token inválido: ¿mismo error que sin token?", auth="invalido"),
    msg("PING;64", S, "esquema en minúsculas 'bearer': ¿se acepta?", auth="bearer " + __import__("prober").TOKEN),
    call("POST", "/__reset", auth="ninguno", seq=S, hipotesis="/__reset sin token: ¿qué responde el original?"),
    call("POST", "/__reset", auth="invalido", seq=S, hipotesis="/__reset con token inválido: ¿qué responde el original?"),
    call("GET", "/", seq=S, hipotesis="raíz: ¿qué responde?"),
    call("GET", "/no-existe", seq=S, hipotesis="ruta inexistente con token: formato del 404"),
    call("GET", "/no-existe", auth="ninguno", seq=S, hipotesis="ruta inexistente sin token: ¿404 o 401 primero?"),
    call("GET", "/msg", seq=S, hipotesis="GET /msg: ¿405 o 404?"),
    call("PUT", "/msg", {"m": "PING;64"}, seq=S, hipotesis="PUT /msg: ¿método no permitido?"),
    call("POST", "/msg/", {"m": "PING;64"}, seq=S, hipotesis="/msg/ con barra final: ¿misma ruta?"),
    call("POST", "/MSG", {"m": "PING;64"}, seq=S, hipotesis="/MSG en mayúsculas: ¿rutas sensibles a mayúsculas?"),
    call("POST", "/health", seq=S, hipotesis="POST /health: ¿método no permitido?"),
    call("GET", "/__reset", seq=S, hipotesis="GET /__reset: ¿método no permitido?"),
]:
    show(e)
