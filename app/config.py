"""Configuración por entorno (ADR-004, ADR-011). Nada sensible vive en el código."""
import os

TEAM_TOKEN = os.environ.get("TEAM_TOKEN", "")
BEHAVIOR_PROFILE = os.environ.get("BEHAVIOR_PROFILE", "v1")
# Railway llama al healthcheck del deploy sin token desde este Host (ADR-004).
HEALTHCHECK_HOSTS = {h.strip().lower() for h in os.environ.get("HEALTHCHECK_HOSTS", "healthcheck.railway.app").split(",") if h.strip()}
