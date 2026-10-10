"""Exp 06 — Formato del campo de control, PING, mensajes sin ';' y caracteres no alfanuméricos.

CONSULTA;AC-0001 tiene control 14 (log 1252). Se varía solo la forma del control.
"""
from control_model import control
from prober import msg, reset, show

S = "s6-control-formato"
reset(S, "estado limpio: formato del control")

B = "CONSULTA;AC-0001"  # control 14; la cuenta no existe tras el reset -> éxito de control = E401
CASOS = [
    (f"{B};014", "cero a la izquierda '014': si se parsea como entero vale 14 -> E401; si se compara texto -> E202"),
    (f"{B};0014", "dos ceros a la izquierda '0014' -> igual que '014'"),
    (f"{B};111", "14+97=111: si compara mod 97 -> E401; si exige rango 2..98 -> E202"),
    (f"{B};-83", "14-97=-83 negativo: '-' no es dígito -> esperamos E201 (mal formado)"),
    (f"{B};+14", "'+14': si usa parseInt/Number acepta -> E401; si exige solo dígitos -> E201"),
    (f"{B}; 14", "espacio antes del control: ¿trim? -> E401, o E201"),
    (f"{B};14 ", "espacio después del control: ¿trim? -> E401, o E201"),
    (f"{B};", "control vacío -> esperamos E201 control mal formado"),
    (f"{B};14.0", "control decimal '14.0' -> esperamos E201"),
    (f"{B};１４", "dígitos de ancho completo '１４' -> esperamos E201 (no ASCII)"),
    (f"{B};0x0E", "hexadecimal 0x0E=14 -> esperamos E201"),
    (f"{B};1e1", "notación científica -> esperamos E201"),
    ("PING;XX", "README: PING;XX responde pong -> ¿PING ignora el control? esperamos 200 o E201"),
    ("PING;63", "PING con control numérico incorrecto (válido 64): ¿E202 o pong?"),
    ("PING;64", "PING con control válido 64 -> pong (reproducción)"),
    ("ping;64", "ping en minúsculas con control 64 -> pong"),
    ("PING", "PING sin ';' ni control -> ¿pong, E201 o E302?"),
    ("PING;", "PING con control vacío -> ¿E201?"),
    (f"PING;X;{control('PING;X')}", "PING con un argumento extra y control válido -> ¿E302 aridad o pong?"),
    ("CONSULTA", "mensaje sin ';' -> ¿E201 (no hay control) o E301/E302?"),
    ("", "mensaje vacío -> ¿E201?"),
    (";", "solo ';' -> comando vacío y control vacío"),
    (f";{control('')}", "comando vacío con control válido de cuerpo vacío (98) -> ¿E301?"),
    ("14", "solo el número -> ¿E201?"),
    (f"SALDOS;AC-0001;{control('SALDOS;AC-0001')}", "comando desconocido con control válido -> E301 (reproducción ejemplo 12)"),
    (f"SALDOS;AC-0001;{control('SALDOS;AC-0001') % 97 + 1}", "comando desconocido + control numérico inválido: ¿E202 o E301? (precedencia)"),
    ("SALDOS;AC-0001;XX", "comando desconocido + control no numérico: ¿E201 o E301? (precedencia)"),
    (f"CONSULTA;AC-0001;X;{control('CONSULTA;AC-0001;X') % 97 + 1}", "aridad mala + control inválido -> E202 antes que E302 (repite 405)"),
    (f"CONSULTA;{control('CONSULTA')}", "CONSULTA sin argumentos con control válido -> E302"),
]
for m, h in CASOS:
    show(msg(m, S, h))
