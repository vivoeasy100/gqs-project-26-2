"""Dependências de injeção e segurança para o FastAPI."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.usuario import Usuario
from repositories.curso_repository import CursoRepository
from repositories.usuario_repository import UsuarioRepository
from services.auth_service import AuthService
from services.curso_service import CursoService
from services.email_service import EmailService

# Instâncias globais da aplicação (in-memory)
usuario_repo = UsuarioRepository()
curso_repo = CursoRepository()
email_service = EmailService()
auth_service = AuthService(usuario_repo)
curso_service = CursoService(curso_repo, email_service)

# Coordenador inicial padrão (para testes e uso inicial do sistema)
auth_service.cadastrar_coordenador_inicial(
    nome="Coordenador do Sistema",
    email="coordenador@cursoseduca.com.br",
    senha="admin_secret_password",
)

security_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return auth_service


def get_curso_service() -> CursoService:
    return curso_service


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    auth_svc: AuthService = Depends(get_auth_service),
) -> Usuario:
    """Extrai e valida usuário logado via Bearer Token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    usuario = auth_svc.obter_usuario_por_token(token)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def require_coordenador(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Exige que o usuário autenticado possua perfil de Coordenador."""
    if not current_user.eh_coordenador():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita à coordenação de cursos",
        )
    return current_user


def require_aluno(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Exige que o usuário autenticado possua perfil de Aluno."""
    if current_user.eh_coordenador():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação destinada apenas a alunos",
        )
    return current_user

