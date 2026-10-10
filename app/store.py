"""Puerto de estado + adaptador en memoria (ADR-002, ADR-012).

El estado se separa por token como en el original. Escalar = otro adaptador (p. ej. Redis
particionado por token) con la misma interfaz; el dominio no cambia. Se despliega 1 réplica a propósito.
"""
from typing import Protocol

from .domain import Estado, estado_inicial


class StateStore(Protocol):
    def get(self, token: str) -> Estado: ...
    def reset(self, token: str) -> None: ...


class InMemoryStore:
    def __init__(self):
        self._estados: dict[str, Estado] = {}

    def get(self, token: str) -> Estado:
        if token not in self._estados:
            self._estados[token] = estado_inicial()
        return self._estados[token]

    def reset(self, token: str) -> None:
        self._estados[token] = estado_inicial()
