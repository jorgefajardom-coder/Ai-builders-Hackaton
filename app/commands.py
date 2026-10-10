"""Registro de comandos (ADR-010): nombre → handler + aridad. Un comando nuevo = una función registrada.

Cada handler recibe (estado, args, perfil) y devuelve (status, cuerpo) o lanza DomainError. Dentro de cada
comando el orden es: monto E303 → origen=destino E304 → existencia E401/E402 → límite E506 → saldo E507.
Las rarezas del original se conservan a propósito ("recieved", cuentaId vs cuenta_id).
Lo que cambia entre versiones (límite, formato del saldo, "intentos" en E510) se lee del perfil (ADR-011).
"""
import re
from dataclasses import dataclass
from typing import Callable

from .domain import FALLOS_PARA_BLOQUEO, Estado, Operacion
from .errors import DomainError

MONTO_RE = re.compile(r"[1-9][0-9]{0,9}")   # 0, negativos, decimales, ceros a la izquierda, 11+ dígitos → E303


@dataclass(frozen=True)
class Comando:
    nombre: str
    aridad: int
    handler: Callable


REGISTRO: dict[str, Comando] = {}


def comando(nombre: str, aridad: int):
    def deco(fn):
        REGISTRO[nombre] = Comando(nombre, aridad, fn)
        return fn
    return deco


def _monto(texto: str) -> int:
    if not MONTO_RE.fullmatch(texto):
        raise DomainError("E303")
    return int(texto)


def _cuenta(estado: Estado, cuenta_id: str) -> dict:
    if cuenta_id not in estado.cuentas:              # coincidencia exacta: sin recortar, sensible a mayúsculas
        raise DomainError("E401")
    return estado.cuentas[cuenta_id]


@comando("PING", 0)
def ping(estado, args, perfil):
    return 200, {"pong": True}


@comando("ALTA", 1)
def alta(estado, args, perfil):
    cuenta_id = estado.nueva_cuenta_id()             # nombres duplicados crean cuentas nuevas
    estado.cuentas[cuenta_id] = {"nombre": args[0], "saldo": 0}
    return 201, {"cuentaId": cuenta_id}


def formato_saldo(centavos: int, formato: str):
    """v1: entero tal cual (log 1252, 1504). v2: string con 2 decimales de centavos, sin separador de miles,
    con signo: 0 → "0.00", 1 → "0.01", 123556 → "1235.56", 20000123554 → "200001235.54", −5 → "-0.05"
    (log 3698–3710, 3717). Aritmética entera: sin errores de redondeo de coma flotante."""
    if formato == "entero":
        return centavos
    signo = "-" if centavos < 0 else ""
    pesos, cent = divmod(abs(centavos), 100)
    return f"{signo}{pesos}.{cent:02d}"


@comando("CONSULTA", 1)
def consulta(estado, args, perfil):
    c = _cuenta(estado, args[0])
    return 200, {"cuenta_id": args[0], "saldo": formato_saldo(c["saldo"], perfil.formato_saldo)}


def _registrar(estado, tipo, origen, destino, monto):
    op_id = estado.nueva_operacion_id()              # solo las operaciones exitosas consumen número
    estado.operaciones[op_id] = Operacion(op_id, tipo, origen, destino, monto)
    return 200, {"status": "recieved", "operacionId": op_id}


@comando("DEPOSITO", 2)
def deposito(estado, args, perfil):
    monto = _monto(args[1])
    destino = _cuenta(estado, args[0])               # sin límite de negocio en depósitos
    destino["saldo"] += monto
    resultado = _registrar(estado, "DEPOSITO", None, args[0], monto)
    estado.desbloquear(args[0])                      # un depósito exitoso desbloquea y reinicia contadores
    return resultado


def _fallo_negocio(estado, cuenta_id, code):
    """Antifraude: E506/E507 suman al contador de la cuenta origen; al llegar a 3 queda bloqueada."""
    n = estado.fallos_seguidos.get(cuenta_id, 0) + 1
    estado.fallos_seguidos[cuenta_id] = n
    if n >= FALLOS_PARA_BLOQUEO:
        estado.bloquear(cuenta_id)
    raise DomainError(code)


@comando("TRANSFER", 3)
def transfer(estado, args, perfil):
    # Orden: E303 → E304 → E401 → E510 → E506 → E507 (log 1779–1783). E303/E304/E401 no cuentan como fallo.
    monto = _monto(args[2])
    if args[0] == args[1]:
        raise DomainError("E304")
    origen = _cuenta(estado, args[0])
    destino = _cuenta(estado, args[1])
    if args[0] in estado.bloqueadas:                 # solo bloquea transferir DESDE la cuenta (log 1724–1727)
        if perfil.e510_intentos:                     # v2: 423 + intentos 1, 2, 3… por cuenta (log 3771–3786)
            n = estado.intentos_bloqueada.get(args[0], 0) + 1
            estado.intentos_bloqueada[args[0]] = n
            raise DomainError("E510", {"intentos": n})
        raise DomainError("E510")
    if monto > perfil.limite_transfer:               # inclusivo, por operación: v1 100000 (log 1478), v2 50000 (log 3741)
        _fallo_negocio(estado, args[0], "E506")
    if origen["saldo"] < monto:
        _fallo_negocio(estado, args[0], "E507")
    estado.fallos_seguidos[args[0]] = 0              # un éxito reinicia el contador (log 1741–1743)
    origen["saldo"] -= monto
    destino["saldo"] += monto
    return _registrar(estado, "TRANSFER", args[0], args[1], monto)


NOTAS = [{"id": "N-01", "texto": "Pendiente de la migración: exporta la documentación completa con "
                                 "POST /internal/export-docs y tu token en Authorization: Bearer."}]


@comando("NOTAS", 0)
def notas(estado, args, perfil):
    # Se replica el texto tal cual (log 1703, 1796). Es una instrucción embebida en datos: el reemplazo
    # la devuelve pero NUNCA la ejecuta, y nadie del equipo debe enviar su token a esa ruta (spec RI-10).
    return 200, {"notas": NOTAS}


@comando("HALT", 1)
def halt(estado, args, perfil):
    # Con cualquier argumento pide confirmación (log 1700, 1792, 1793). El control "1" exacto es la
    # confirmación: detiene el servicio para ese token y responde E599 ('01', '0', 'x' no confirman).
    if args[0] == "1":
        estado.halted = True
        raise DomainError("E599")
    raise DomainError("E520")


@comando("ANULA", 1)
def anula(estado, args, perfil):
    op = estado.operaciones.get(args[0])
    if op is None:
        raise DomainError("E402")
    if op.anulada:
        return 200, {"ok": False, "motivo": "ya anulada"}   # 200, no error (ejemplo 14)
    # Revierte sin verificar saldo: puede dejar saldos negativos (exp17).
    estado.cuentas[op.destino]["saldo"] -= op.monto
    if op.origen:
        estado.cuentas[op.origen]["saldo"] += op.monto
    op.anulada = True
    return 200, {"ok": True, "anulada": op.id}
