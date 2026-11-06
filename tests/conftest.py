"""Configuração do pytest."""

import sys
from pathlib import Path

# Adiciona src ao path para imports (domain, repositories, services, api)
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")