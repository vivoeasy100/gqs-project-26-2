"""Rotas de Autenticação e Gestão de Contas (US-04 e US-05)."""

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import (
    get_auth_service,
    get_current_user,
    security_scheme,
)
from api.schemas import (
    LoginResponse,
    UsuarioCadastroRequest,
    UsuarioLoginRequest,
    UsuarioResponse,
)
from domain.exceptions import UsuarioInvalido
from domain.usuario import Usuario
from services.auth_service import (
    AuthService,
    CredenciaisInvalidas,
    EmailJaCadastrado,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="US-04: Criar conta de aluno",
)
def register(
    req: UsuarioCadastroRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> UsuarioResponse:
    """US-04: Cadastra uma nova conta de aluno com e-mail único e formato válido."""
    try:
        usuario = auth_svc.criar_conta_aluno(
            nome=req.nome,
            email=req.email,
            senha=req.senha,
        )
        return UsuarioResponse(
            nome=usuario.nome,
            email=usuario.email,
            perfil=usuario.perfil.value,
        )
    except EmailJaCadastrado as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except UsuarioInvalido as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="US-05: Fazer login no sistema",
)
def login(
    req: UsuarioLoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """US-05: Autentica com e-mail e senha, retornando mensagem genérica em caso de falha."""
    try:
        usuario, token = auth_svc.login(email=req.email, senha=req.senha)
        return LoginResponse(
            access_token=token,
            usuario=UsuarioResponse(
                nome=usuario.nome,
                email=usuario.email,
                perfil=usuario.perfil.value,
            ),
        )
    except CredenciaisInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        ) from exc


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="US-05: Obter dados do usuário logado",
)
def get_me(current_user: Usuario = Depends(get_current_user)) -> UsuarioResponse:
    """Retorna os dados do perfil ativo."""
    return UsuarioResponse(
        nome=current_user.nome,
        email=current_user.email,
        perfil=current_user.perfil.value,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="US-05 c3: Encerrar sessão",
)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    auth_svc: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """US-05 c3: Invalida o token de sessão atual."""
    if credentials and credentials.credentials:
        auth_svc.logout(credentials.credentials)
    return {"message": "Sessão encerrada com sucesso"}

