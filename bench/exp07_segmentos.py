"""Exp 07 — Longitud del control (¿1–2 dígitos?), segmentos vacíos y precedencia E103/E104/E201/E202/E301/E302."""
from control_model import control
from prober import msg, reset, show

S = "s7-segmentos"
reset(S, "estado limpio: longitud del control y segmentos vacíos")

c = control
CASOS = [
    ("CONSULTA;AC-0100;08", "control 8 escrito '08' (2 caracteres con cero): si el formato es ^\\d{1,2}$ -> E401; si prohíbe ceros a la izquierda -> E201"),
    ("CONSULTA;AC-0100;8", "control 8 sin cero -> E401 (reproduce 178)"),
    ("CONSULTA;AC-0001;99", "99 tiene 2 dígitos pero fuera del rango 2..98 -> esperamos E202"),
    ("CONSULTA;AC-0001;0", "control 0 -> E202 (formato válido, valor incorrecto)"),
    ("CONSULTA;AC-0001;00", "control '00' -> E202 si se aceptan 2 dígitos con cero"),
    ("CONSULTA;AC-0001;100", "control de 3 dígitos sin cero inicial -> E201 si el límite es 2 caracteres"),
    ("CONSULTA;A;98", "control 98 válido -> E401 (reproduce 1160)"),
    ("CONSULTA;;14", "segmento de argumento vacío con control válido de 'CONSULTA;' (14?) -> E104 antes que control"),
    (f"CONSULTA;;{c('CONSULTA;')}", "argumento vacío con control válido -> E104 segmento vacío"),
    ("CONSULTA;;XX", "argumento vacío + control mal formado: ¿E104 o E201 primero?"),
    (";AC-0001;XX", "comando vacío + control mal formado: ¿E104 o E201?"),
    ("PING;X;XX", "PING con aridad mala + control mal formado: ¿PING valida control cuando la aridad es mala? E302 o E201"),
    ("PING;X;", "PING con último segmento vacío -> E104"),
    ("PING;;64", "PING con segmento intermedio vacío -> E104 o E302"),
    (f"SALDOS;A;B;C;{c('SALDOS;A;B;C')}", "comando desconocido con muchos args y control válido -> E301 (no hay aridad que comprobar)"),
    (f"CONSULTA ;AC-0001;{c('CONSULTA ;AC-0001')}", "espacio tras el comando: el espacio no cuenta en el control; ¿se recorta el comando? -> E401 o E301"),
    (f"CONSULTA; AC-0001;{c('CONSULTA; AC-0001')}", "espacio antes del id de cuenta: ¿recorte -> E401 genérico? (la cuenta no existe igual)"),
    (f"PING ;{c('PING')}", "'PING ' con espacio: ¿se recorta? -> pong o E301"),
    (" PING;64", "espacio inicial ' PING' -> pong si recorta, E301 si no"),
]
for m, h in CASOS:
    show(msg(m, S, h))
