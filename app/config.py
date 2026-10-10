"""Configuración por entorno (ADR-004, ADR-011). Nada sensible vive en el código."""
import os

TEAM_TOKEN = os.environ.get("TEAM_TOKEN", "").strip()   # un salto de línea pegado en Railway no debe dar 401 a todo
BEHAVIOR_PROFILE = os.environ.get("BEHAVIOR_PROFILE", "v2")   # v2 = versión vigente del original (spec §6); v1 por env
# Railway llama al healthcheck del deploy sin token desde este Host (ADR-004).
HEALTHCHECK_HOSTS = {h.strip().lower() for h in os.environ.get("HEALTHCHECK_HOSTS", "healthcheck.railway.app").split(",") if h.strip()}
