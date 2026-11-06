"""Entidade: Modulo (Passo 2 e 3).

Regras:
- US-02 c4: Link precisa ser uma URL
"""

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

from .exceptions import ModuloInvalido


@dataclass(slots=True)
class Modulo:
    """Módulo de um curso."""

    titulo: str
    link: str
    data: date | None = None  # Só obrigatório no síncrono (US-02 c3)

    def __post_init__(self) -> None:
        self._validar_link()

    def _validar_link(self) -> None:
        """US-02 c4: Link precisa ser uma URL válida."""
        parsed = urlparse(self.link)
        if not parsed.scheme or not parsed.netloc:
            raise ModuloInvalido(f"Link inválido: '{self.link}'. Deve ser uma URL completa.")