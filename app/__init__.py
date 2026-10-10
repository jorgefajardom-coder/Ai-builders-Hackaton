"""Reemplazo del servicio "caja negra". Arquitectura hexagonal mínima (ver docs/02 Arquitectura).

http_adapter (borde ASGI) → pipeline (etapas ordenadas) → commands (registro) → domain (puro) → store (puerto)
El perfil de comportamiento (profiles/) define orden de etapas, catálogo de errores y comandos activos.
"""
