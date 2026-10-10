"""Perfiles de comportamiento (ADR-011). v2 hereda de v1 y sobrescribe solo lo que cambió (15:50–15:55).

Se elige con BEHAVIOR_PROFILE (por defecto v2, la versión vigente; v1 sigue disponible). Los comandos leen
del perfil que reciben los parámetros que cambian entre versiones; el diff V1 → V2 ES el incidente (spec §6):

  CB-04 · formato_saldo   "entero" → "decimal2": CONSULTA devuelve el saldo (centavos) como string "1235.56"
  CB-05 · limite_transfer 100000 → 50000 (inclusivo, por operación)
  CB-06 · E510            409 → 423 y el cuerpo agrega "intentos" (E510 de esa cuenta desde que se bloqueó)
"""
from dataclasses import dataclass, field, replace

from .errors import CATALOG_V1, ErrorSpec


@dataclass(frozen=True)
class Perfil:
    nombre: str
    catalogo: dict
    orden_msg: tuple = ("tamano", "json", "campo_m", "separador", "segmentos", "ping",
                        "control_formato", "control_valor", "comando", "aridad")
    rutas: dict = field(default_factory=lambda: {("GET", "/health"): "health",
                                                 ("POST", "/__reset"): "reset",
                                                 ("POST", "/msg"): "msg"})
    limite_transfer: int = 100_000      # máximo por TRANSFER, inclusivo (v1: log 1477, 1478)
    formato_saldo: str = "entero"       # "entero" (v1) | "decimal2" (v2)
    e510_intentos: bool = False         # v2: E510 lleva "intentos"


V1 = Perfil("v1", CATALOG_V1)

CATALOG_V2 = {**CATALOG_V1,
              "E510": ErrorSpec(423, "cuenta bloqueada", "log 3580, 3581, 3771, 3778, 3783–3786 — v2 (CB-06)")}

V2 = replace(V1, nombre="v2", catalogo=CATALOG_V2,
             limite_transfer=50_000,        # log 3740, 3741, 3747, 3748 (CB-05)
             formato_saldo="decimal2",      # log 3698–3710, 3717 (CB-04)
             e510_intentos=True)            # log 3771–3805 (CB-06)

PERFILES = {"v1": V1, "v2": V2}


def cargar(nombre: str) -> Perfil:
    return PERFILES.get(nombre, V2)
