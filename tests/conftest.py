"""
Configuración y fixtures comunes para tests.
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_fixture():
    """Proporciona la ruta raíz del proyecto."""
    return project_root


@pytest.fixture
def logs_dir():
    """Proporciona el directorio de logs."""
    return project_root / "logs"
