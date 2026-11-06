"""Serviço de Autenticação e Gestão de Usuários (US-04 e US-05)."""

import hashlib
import hmac
import secrets
from threading import Lock
from domain.enums import Perfil
from domain.exceptions import UsuarioInvalido
from domain.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository


class CredenciaisInvalidas(Exception):
    """Mensagem de erro genérica para login incorreto (US-05 c2)."""
    pass


class EmailJaCadastrado(Exception):
    """E-mail duplicado no cadastro de aluno (US-04 c2)."""
    pass


class AuthService:
    """Gerencia cadastro de alunos, hash seguro de senhas e tokens de sessão."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self.usuario_repo = usuario_repo
        self._sessoes: dict[str, str] = {}  # token -> email
        self._lock = Lock()

    @staticmethod
    def _hash_senha(senha: str, salt: str | None = None) -> str:
        """Gera hash PBKDF2 com salt embutido."""
        if salt is None:
            salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return f"{salt}${key.hex()}"

    @classmethod
    def _verificar_senha(cls, senha: str, hash_armazenado: str) -> bool:
        """Valida a senha contra o hash armazenado."""
        try:
            salt, hash_hex = hash_armazenado.split("$")
            novo_hash = hashlib.pbkdf2_hmac(
                "sha256",
                senha.encode("utf-8"),
                salt.encode("utf-8"),
                iterations=100_000,
            ).hex()
            return hmac.compare_digest(hash_hex, novo_hash)
        except Exception:
            return False

    def cadastrar_coordenador_inicial(
        self, nome: str, email: str, senha: str
    ) -> Usuario:
        """Cria um coordenador direto no sistema (fora de tela pública conforme US-04)."""
        email_clean = email.strip()
        senha_hash = self._hash_senha(senha)
        usuario = Usuario(
            nome=nome.strip(),
            email=email_clean,
            senha_hash=senha_hash,
            perfil=Perfil.COORDENADOR,
        )
        return self.usuario_repo.salvar(usuario)

    def criar_conta_aluno(self, nome: str, email: str, senha: str) -> Usuario:
        """US-04: Cria conta de aluno com validação de unicidade e formato de e-mail."""
        email_clean = email.strip()
        if not nome or not nome.strip():
            raise UsuarioInvalido("Nome completo é obrigatório")
        if not senha or not senha.strip():
            raise UsuarioInvalido("Senha é obrigatória")

        if self.usuario_repo.existe_email(email_clean):
            raise EmailJaCadastrado(f"E-mail '{email_clean}' já possui cadastro. Faça login.")

        senha_hash = self._hash_senha(senha)
        # O construtor do Usuario valida o formato do e-mail (US-04 c3)
        usuario = Usuario(
            nome=nome.strip(),
            email=email_clean,
            senha_hash=senha_hash,
            perfil=Perfil.ALUNO,
        )
        return self.usuario_repo.salvar(usuario)

    def login(self, email: str, senha: str) -> tuple[Usuario, str]:
        """US-05 c1, c2: Realiza login e gera token de sessão com mensagem genérica em caso de erro."""
        usuario = self.usuario_repo.buscar_por_email(email)
        if not usuario or not self._verificar_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidas("E-mail ou senha incorretos")

        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessoes[token] = usuario.email.lower().strip()
        return usuario, token

    def logout(self, token: str) -> bool:
        """US-05 c3: Termina a sessão do usuário."""
        with self._lock:
            return self._sessoes.pop(token, None) is not None

    def obter_usuario_por_token(self, token: str) -> Usuario | None:
        """Recupera o usuário associado a um token ativo."""
        with self._lock:
            email = self._sessoes.get(token)
        if not email:
            return None
        return self.usuario_repo.buscar_por_email(email)

