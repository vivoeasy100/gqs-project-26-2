"""Entidade: Usuario (Passo 2 e 3).

Regras:
- US-04 c3: E-mail em formato válido
- US-05 c1: Saber se é aluno ou coordenador (eh_coordenador)
"""

from dataclasses import dataclass
from urllib.parse import urlparse

from .enums import Perfil
from .exceptions import UsuarioInvalido


@dataclass(slots=True)
class Usuario:
    """Usuário do sistema (aluno ou coordenador)."""

    nome: str
    email: str
    senha_hash: str
    perfil: Perfil

    def __post_init__(self) -> None:
        self._validar_email()

    def _validar_email(self) -> None:
        """US-04 c3: E-mail em formato válido (validação simples)."""
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            raise UsuarioInvalido(f"E-mail inválido: '{self.email}'")

    def eh_coordenador(self) -> bool:
        """US-05 c1: Verifica se o usuário é coordenador."""
        return self.perfil == Perfil.COORDENADOR