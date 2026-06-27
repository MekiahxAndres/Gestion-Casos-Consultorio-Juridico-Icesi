from __future__ import annotations

import os
from pathlib import Path


BASE_URL = os.getenv("CJ_BASE_URL", "https://consultorio-juridico-icesi.up.railway.app").rstrip("/")
HEADLESS = os.getenv("CJ_HEADLESS", "true").lower() not in {"0", "false", "no"}
TIMEOUT = int(os.getenv("CJ_TIMEOUT", "20"))

SELENIUM_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = SELENIUM_DIR / "screenshots" / "final_sprint"


ROLE_CREDENTIALS = {
    "secretaria": {
        "document": os.getenv("CJ_SECRETARIA_DOC"),
        "password": os.getenv("CJ_SECRETARIA_PASSWORD"),
        "expected_panel": "Panel de Secretaria",
    },
    "asesor": {
        "document": os.getenv("CJ_ASESOR_DOC"),
        "password": os.getenv("CJ_ASESOR_PASSWORD"),
        "expected_panel": "Panel de Supervision",
    },
    "estudiante": {
        "document": os.getenv("CJ_ESTUDIANTE_DOC"),
        "password": os.getenv("CJ_ESTUDIANTE_PASSWORD"),
        "expected_panel": "Mi Caso Asignado",
    },
    "beneficiario": {
        "document": os.getenv("CJ_BENEFICIARIO_DOC"),
        "password": os.getenv("CJ_BENEFICIARIO_PASSWORD"),
        "expected_panel": "Panel",
    },
}


REQUIRED_TAGS = {
    "requires_secretaria": "secretaria",
    "requires_asesor": "asesor",
    "requires_estudiante": "estudiante",
    "requires_beneficiario": "beneficiario",
}


def credentials_for(role: str) -> dict[str, str | None]:
    return ROLE_CREDENTIALS[role]


def has_credentials(role: str) -> bool:
    credentials = credentials_for(role)
    return bool(credentials.get("document") and credentials.get("password"))
