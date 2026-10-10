"""Registro de comandos (ADR-010): nombre → handler + aridad. Un comando nuevo = una función registrada.

Cada handler recibe (estado, args) y devuelve (status, cuerpo) o lanza DomainError. Dentro de cada
comando el orden es: monto E303 → origen=destino E304 → existencia E401/E402 → límite E506 → saldo E507.
Las rarezas del original se conservan a propósito ("recieved", cuentaId vs cuenta_id).
"""
import re
from dataclasses import dataclass
from typing import Callable

from .domain import LIMITE_OPERACION, Estado, Operacion
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
def ping(estado, args):
    return 200, {"pong": True}


@comando("ALTA", 1)
def alta(estado, args):
    cuenta_id = estado.nueva_cuenta_id()             # nombres duplicados crean cuentas nuevas
    estado.cuentas[cuenta_id] = {"nombre": args[0], "saldo": 0}
    return 201, {"cuentaId": cuenta_id}


@comando("CONSULTA", 1)
def consulta(estado, args):
    c = _cuenta(estado, args[0])
    return 200, {"cuenta_id": args[0], "saldo": c["saldo"]}


def _registrar(estado, tipo, origen, destino, monto):
    op_id = estado.nueva_operacion_id()              # solo las operaciones exitosas consumen número
    estado.operaciones[op_id] = Operacion(op_id, tipo, origen, destino, monto)
    return 200, {"status": "recieved", "operacionId": op_id}


@comando("DEPOSITO", 2)
def deposito(estado, args):
    monto = _monto(args[1])
    destino = _cuenta(estado, args[0])               # sin límite de negocio en depósitos
    destino["saldo"] += monto
    return _registrar(estado, "DEPOSITO", None, args[0], monto)


@comando("TRANSFER", 3)
def transfer(estado, args):
    monto = _monto(args[2])
    if args[0] == args[1]:
        raise DomainError("E304")
    origen = _cuenta(estado, args[0])
    destino = _cuenta(estado, args[1])
    if monto > LIMITE_OPERACION:                     # ≤ 100000 inclusivo, por operación (log 1478)
        raise DomainError("E506")
    if origen["saldo"] < monto:
        raise DomainError("E507")
    origen["saldo"] -= monto
    destino["saldo"] += monto
    return _registrar(estado, "TRANSFER", args[0], args[1], monto)


@comando("ANULA", 1)
def anula(estado, args):
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
