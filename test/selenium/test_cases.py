"""
Launcher de pruebas funcionales Selenium/Behave.

Uso recomendado desde la raiz del proyecto:

    venv\\Scripts\\python.exe test\\selenium\\test_cases.py

Para ejecutar escenarios autenticados contra el despliegue, configurar antes:

    $env:CJ_SECRETARIA_DOC="..."
    $env:CJ_SECRETARIA_PASSWORD="..."
    $env:CJ_ASESOR_DOC="..."
    $env:CJ_ASESOR_PASSWORD="..."
    $env:CJ_ESTUDIANTE_DOC="..."
    $env:CJ_ESTUDIANTE_PASSWORD="..."
    $env:CJ_BENEFICIARIO_DOC="..."
    $env:CJ_BENEFICIARIO_PASSWORD="..."
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
FEATURES_DIR = BASE_DIR / "features"


def main() -> int:
    command = [
        sys.executable,
        "-m",
        "behave",
        str(FEATURES_DIR),
        "--format",
        "pretty",
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
