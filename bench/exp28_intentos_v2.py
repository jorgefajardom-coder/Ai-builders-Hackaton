"""Exp 28 — Incidente v2: E510 pasa a 423 y agrega "intentos" (CB-06).

Regresión: intentos = 1, 2, 3… en E510 sucesivos (log 3580–3581, 3640–3641, 3675–3679); los fallos de
validación previos (E303/E304/E401) no lo movieron (3637–3640). Preguntas: ¿cuenta por cuenta? ¿lo mueven
E302/E303/E304/E401 cuando la cuenta YA está bloqueada? ¿lo mueven CONSULTA/DEPOSITO fallido/ANULA? ¿un DEPOSITO
que desbloquea lo reinicia (al re-bloquear vuelve a 1)? ¿el umbral sigue en 3 seguidas y el éxito reinicia?
¿transferir HACIA la cuenta bloqueada sigue permitido?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.checkval import control  # noqa: E402
from prober import msg, reset, show  # noqa: E402


def m(body, seq, hip):
    show(msg(f"{body};{control(body)}", seq, hip))


def bloquear(seq, cuenta, otra):
    for i in range(1, 4):
        m(f"TRANSFER;{cuenta};{otra};5000", seq, f"E507 #{i} desde {cuenta} (bloqueo a la 3.ª)")


S = "s28a-intentos-contador"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("ALTA;Caro", S, "AC-0003")
m("DEPOSITO;AC-0001;1000", S, "saldo 1000 en AC-0001")
m("DEPOSITO;AC-0002;1000", S, "saldo 1000 en AC-0002")
bloquear(S, "AC-0001", "AC-0002")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: primer intento bloqueado → 423 intentos 1")
m("TRANSFER;AC-0001;AC-0002;0", S, "v2: E303 con la cuenta bloqueada → E303 (¿suma a intentos?)")
m("TRANSFER;AC-0001;AC-0001;10", S, "v2: E304 con la cuenta bloqueada (¿suma?)")
m("TRANSFER;AC-0001;AC-0009;10", S, "v2: E401 con la cuenta bloqueada (¿suma?)")
m("TRANSFER;AC-0001;AC-0002", S, "v2: E302 con la cuenta bloqueada (¿suma?)")
m("CONSULTA;AC-0001", S, "v2: CONSULTA de la bloqueada (¿suma?)")
m("ANULA;OP-0001", S, "v2: ANULA del depósito de la bloqueada (¿suma?); saldo AC-0001 → 0")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: ¿intentos 2 (validaciones/otros comandos no cuentan) o más?")
m("TRANSFER;AC-0002;AC-0001;100", S, "v2: transferir HACIA la bloqueada → 200 (solo bloquea el origen)")
bloquear(S, "AC-0002", "AC-0003")
m("TRANSFER;AC-0002;AC-0003;100", S, "v2: otra cuenta bloqueada → ¿su propio contador empieza en 1?")
m("TRANSFER;AC-0001;AC-0003;100", S, "v2: AC-0001 de nuevo → ¿3 (contador por cuenta)?")
m("TRANSFER;AC-0002;AC-0003;100", S, "v2: AC-0002 → ¿2?")
m("TRANSFER;AC-0001;AC-0002;999999", S, "v2: monto sobre el límite con la cuenta bloqueada → E510 (antes que E506), ¿intentos 4?")

S = "s28b-intentos-desbloqueo"
reset(S)
m("ALTA;Ana", S, "AC-0001")
m("ALTA;Beto", S, "AC-0002")
m("DEPOSITO;AC-0001;1000", S, "saldo 1000")
bloquear(S, "AC-0001", "AC-0002")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: intentos 1")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: intentos 2")
m("DEPOSITO;AC-0001;10", S, "DEPOSITO exitoso: desbloquea (CT-12, ¿sigue en v2?)")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: tras desbloquear → 200")
m("TRANSFER;AC-0001;AC-0002;5000", S, "E507 #1 tras desbloqueo")
m("TRANSFER;AC-0001;AC-0002;5000", S, "E507 #2")
m("TRANSFER;AC-0001;AC-0002;100", S, "éxito con 2 fallos → 200 (umbral sigue en 3 y el éxito reinicia)")
bloquear(S, "AC-0001", "AC-0002")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: re-bloqueada → ¿intentos vuelve a 1 o sigue en 3?")
m("TRANSFER;AC-0001;AC-0002;100", S, "v2: siguiente → ¿2?")
