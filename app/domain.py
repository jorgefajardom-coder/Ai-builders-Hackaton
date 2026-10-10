"""Núcleo de dominio puro (ADR-008): estado + reglas, sin I/O, reloj ni azar.

El estado incluye los contadores de IDs, así /__reset los reinicia también (ADR-002).
"""
from dataclasses import dataclass, field

FALLOS_PARA_BLOQUEO = 3     # 3 TRANSFER seguidas con E506/E507 bloquean la cuenta origen (log 1719–1722, 1748–1751)


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
    fallos_seguidos: dict = field(default_factory=dict)  # cuentaId -> TRANSFER fallidas seguidas (solo E506/E507)
    bloqueadas: set = field(default_factory=set)         # cuentas que ya no pueden transferir (E510)
    intentos_bloqueada: dict = field(default_factory=dict)  # v2: cuentaId -> E510 recibidos desde el bloqueo
    seq_cuenta: int = 0
    seq_operacion: int = 0
    halted: bool = False                              # HALT confirmado (control "1") → E599 en /msg

    def bloquear(self, cuenta_id: str) -> None:
        self.bloqueadas.add(cuenta_id)
        self.intentos_bloqueada[cuenta_id] = 0           # cada bloqueo nuevo vuelve a contar desde 1 (log 3804)

    def desbloquear(self, cuenta_id: str) -> None:
        self.bloqueadas.discard(cuenta_id)
        self.intentos_bloqueada.pop(cuenta_id, None)
        self.fallos_seguidos[cuenta_id] = 0

    def nueva_cuenta_id(self) -> str:
        self.seq_cuenta += 1
        return f"AC-{self.seq_cuenta:04d}"

    def nueva_operacion_id(self) -> str:
        self.seq_operacion += 1
        return f"OP-{self.seq_operacion:04d}"


def estado_inicial() -> Estado:
    return Estado()
