"""Catálogo de errores como datos (ADR-009). Cuerpos exactos del original, rarezas incluidas.

Cada perfil puede sobrescribir entradas (ADR-011). Evidencia = ids de experimentos.jsonl / ejemplos.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorSpec:
    status: int
    mensaje: str
    evidencia: str


CATALOG_V1 = {
    "E001": ErrorSpec(401, "no autorizado", "log 2, 5–9"),
    "E100": ErrorSpec(400, "json inválido", "log 1366"),
    "E101": ErrorSpec(413, "cuerpo demasiado grande", "log 1384 (> 8192 bytes)"),
    "E102": ErrorSpec(400, "falta m", "log 1369"),
    "E103": ErrorSpec(400, "falta control", "log 1278"),
    "E104": ErrorSpec(400, "segmento vacío", "log 1269"),
    "E201": ErrorSpec(400, "control mal formado", "ejemplo 17, log 1262"),
    "E202": ErrorSpec(400, "control inválido", "ejemplo 2, log 20"),
    "E301": ErrorSpec(400, "comando desconocido ", "ejemplo 12, log 1286 — espacio final del original"),
    "E302": ErrorSpec(400, "aridad inválida", "ejemplo 20, log 405"),
    "E303": ErrorSpec(400, "monto inválido", "log 1414"),
    "E304": ErrorSpec(400, "origen y destino iguales", "log 1480"),
    "E401": ErrorSpec(404, "cuenta inexistente", "ejemplo 15, log 37"),
    "E402": ErrorSpec(404, "operación inexistente", "log 741"),
    "E404": ErrorSpec(404, "ruta desconocida", "log 10–18"),
    "E506": ErrorSpec(422, "límite excedido", "ejemplo 9, log 1478"),
    "E507": ErrorSpec(422, "saldo insuficiente", "ejemplo 16, log 1537"),
    "E510": ErrorSpec(409, "cuenta bloqueada", "log 1722, 1751, 1782 — antifraude"),
    "E520": ErrorSpec(409, "operación destructiva: detiene el servicio; reenvía con confirmación", "log 1700, 1792 — HALT"),
    "E599": ErrorSpec(503, "service halted", "HALT confirmado con control 1"),
}


class DomainError(Exception):
    """Lo lanzan etapas y comandos; el adaptador HTTP lo traduce con el catálogo del perfil."""

    def __init__(self, code: str, extra: dict | None = None):
        super().__init__(code)
        self.code = code
        self.extra = extra or {}
