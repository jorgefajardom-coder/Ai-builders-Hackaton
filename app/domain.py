"""Núcleo de dominio puro (ADR-008): estado + reglas, sin I/O, reloj ni azar.

El estado incluye los contadores de IDs, así /__reset los reinicia también (ADR-002).
"""
from dataclasses import dataclass, field

LIMITE_OPERACION = 100_000  # 100000 pasa (ejemplo 10), 120000 da E506 (ejemplo 9). Frontera exacta: por confirmar.


@dataclass
class Operacion:
    id: str
    tipo: str            # "DEPOSITO" | "TRANSFER"
    origen: str | None
    destino: str
    monto: int
    anulada: bool = False


@dataclass
class Estado:
    cuentas: dict = field(default_factory=dict)       # cuentaId -> {"nombre": str, "saldo": int}
    operaciones: dict = field(default_factory=dict)   # operacionId -> Operacion
    seq_cuenta: int = 0
    seq_operacion: int = 0

    def nueva_cuenta_id(self) -> str:
        self.seq_cuenta += 1
        return f"AC-{self.seq_cuenta:04d}"

    def nueva_operacion_id(self) -> str:
        self.seq_operacion += 1
        return f"OP-{self.seq_operacion:04d}"


def estado_inicial() -> Estado:
    return Estado()
