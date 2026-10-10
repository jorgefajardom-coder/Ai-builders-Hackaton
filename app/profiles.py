"""Perfiles de comportamiento (ADR-011). v2 hereda de v1 y sobrescribe solo lo que cambie a las 15:30.

Se elige con BEHAVIOR_PROFILE. El diff entre perfiles documenta el incidente (spec §6).
"""
from dataclasses import dataclass, field, replace

from .errors import CATALOG_V1


@dataclass(frozen=True)
class Perfil:
    nombre: str
    catalogo: dict
    orden_msg: tuple = ("tamano", "json", "campo_m", "separador", "segmentos", "ping",
                        "control_formato", "control_valor", "comando", "aridad")
    rutas: dict = field(default_factory=lambda: {("GET", "/health"): "health",
                                                 ("POST", "/__reset"): "reset",
                                                 ("POST", "/msg"): "msg"})


V1 = Perfil("v1", CATALOG_V1)
V2 = replace(V1, nombre="v2")   # overrides del incidente: se completan después de las 15:30

PERFILES = {"v1": V1, "v2": V2}


def cargar(nombre: str) -> Perfil:
    return PERFILES.get(nombre, V1)
