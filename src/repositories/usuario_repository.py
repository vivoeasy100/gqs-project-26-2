"""Repositório de Usuários em memória."""

from threading import Lock
from domain.usuario import Usuario


class UsuarioRepository:
    """Armazenamento em memória de usuários."""

    def __init__(self) -> None:
        self._usuarios: dict[str, Usuario] = {}
        self._lock = Lock()

    def salvar(self, usuario: Usuario) -> Usuario:
        """Salva ou atualiza um usuário por e-mail normalizado."""
        with self._lock:
            self._usuarios[usuario.email.lower().strip()] = usuario
            return usuario

    def buscar_por_email(self, email: str) -> Usuario | None:
        """Busca usuário pelo e-mail (case-insensitive)."""
        with self._lock:
            return self._usuarios.get(email.lower().strip())

    def existe_email(self, email: str) -> bool:
        """Verifica se já existe conta com o e-mail informado."""
        with self._lock:
            return email.lower().strip() in self._usuarios

    def listar(self) -> list[Usuario]:
        """Retorna todos os usuários cadastrados."""
        with self._lock:
            return list(self._usuarios.values())

    def limpar(self) -> None:
        """Limpa o repositório (útil para testes)."""
        with self._lock:
            self._usuarios.clear()

