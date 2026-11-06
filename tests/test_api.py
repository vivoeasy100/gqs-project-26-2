"""Testes de integração das rotas da API FastAPI, schemas e dependências de segurança."""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import (
    get_current_user,
    require_aluno,
    require_coordenador,
)
from api.routes_auth import get_me, login, logout, register
from api.routes_cursos import (
    adicionar_modulo,
    criar_curso,
    editar_curso,
    listar_cursos_publicados,
    obter_detalhes_curso,
    publicar_curso,
    remover_modulo,
)
from api.routes_inscricoes import (
    confirmar_pagamento,
    inscrever_em_curso,
    listar_inscritos,
    listar_meus_cursos,
    obter_meu_curso,
)
from api.schemas import (
    CursoCreateRequest,
    CursoUpdateRequest,
    ModuloCreateRequest,
    UsuarioCadastroRequest,
    UsuarioLoginRequest,
)
from domain.enums import Perfil
from domain.usuario import Usuario
from repositories.curso_repository import CursoRepository
from repositories.usuario_repository import UsuarioRepository
from services.auth_service import AuthService
from services.curso_service import CursoService
from services.email_service import EmailService


@pytest.fixture
def ambiente():
    """Ambiente isolado de repositórios e serviços para teste da API."""
    u_repo = UsuarioRepository()
    c_repo = CursoRepository()
    e_svc = EmailService()
    auth_svc = AuthService(u_repo)
    curso_svc = CursoService(c_repo, e_svc)

    # Coordenador padrão
    coord = auth_svc.cadastrar_coordenador_inicial(
        nome="Coordenador do Sistema",
        email="coordenador@cursoseduca.com.br",
        senha="admin_secret_password",
    )
    return {
        "usuario_repo": u_repo,
        "curso_repo": c_repo,
        "email_service": e_svc,
        "auth_service": auth_svc,
        "curso_service": curso_svc,
        "coordenador": coord,
    }


# --- US-04 e US-05: Autenticação, Cadastro e Sessão ---

def test_api_us04_registro_aluno_sucesso_e_regras(ambiente):
    auth_svc = ambiente["auth_service"]

    # 1. Cadastro com sucesso (US-04 c1)
    req = UsuarioCadastroRequest(
        nome="Ana Paula",
        email="ana@exemplo.com",
        senha="senha_segura_123",
    )
    resp = register(req=req, auth_svc=auth_svc)
    assert resp.nome == "Ana Paula"
    assert resp.email == "ana@exemplo.com"
    assert resp.perfil == "aluno"

    # 2. E-mail duplicado (US-04 c2) -> 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        register(req=req, auth_svc=auth_svc)
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    # 3. E-mail inválido (US-04 c3) -> 400 Bad Request
    req_invalido = UsuarioCadastroRequest(
        nome="Ana Paula",
        email="email_sem_arroba",
        senha="123",
    )
    with pytest.raises(HTTPException) as exc_info:
        register(req=req_invalido, auth_svc=auth_svc)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_api_us05_login_e_controle_sessao(ambiente):
    auth_svc = ambiente["auth_service"]
    auth_svc.criar_conta_aluno("Bruno Costa", "bruno@exemplo.com", "senha_correta")

    # 1. Login com sucesso (US-05 c1)
    req_login = UsuarioLoginRequest(email="bruno@exemplo.com", senha="senha_correta")
    login_resp = login(req=req_login, auth_svc=auth_svc)
    token = login_resp.access_token
    assert token is not None
    assert login_resp.usuario.email == "bruno@exemplo.com"
    assert login_resp.usuario.perfil == "aluno"

    # 2. Obter perfil com token ativo
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user_me = get_current_user(credentials=creds, auth_svc=auth_svc)
    me_resp = get_me(current_user=user_me)
    assert me_resp.email == "bruno@exemplo.com"

    # 3. Login com senha errada -> 401 Unauthorized com mensagem genérica (US-05 c2)
    req_errado = UsuarioLoginRequest(email="bruno@exemplo.com", senha="senha_errada")
    with pytest.raises(HTTPException) as exc_info:
        login(req=req_errado, auth_svc=auth_svc)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "E-mail ou senha incorretos"

    # 4. Logout encerra sessão (US-05 c3)
    logout(credentials=creds, auth_svc=auth_svc)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, auth_svc=auth_svc)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_api_autorizacao_perfis(ambiente):
    coord = ambiente["coordenador"]
    aluno = ambiente["auth_service"].criar_conta_aluno("Aluno X", "aluno@x.com", "pass")

    # Coordenador passa no require_coordenador
    assert require_coordenador(coord) == coord

    # Aluno é rejeitado no require_coordenador com 403 Forbidden
    with pytest.raises(HTTPException) as exc_coord:
        require_coordenador(aluno)
    assert exc_coord.value.status_code == status.HTTP_403_FORBIDDEN

    # Aluno passa no require_aluno
    assert require_aluno(aluno) == aluno

    # Coordenador é rejeitado no require_aluno com 403 Forbidden
    with pytest.raises(HTTPException) as exc_aluno:
        require_aluno(coord)
    assert exc_aluno.value.status_code == status.HTTP_403_FORBIDDEN


# --- US-01, US-02, US-03, US-06: Cursos e Módulos ---

def test_api_fluxo_curso_coordenador_e_aluno(ambiente):
    coord = ambiente["coordenador"]
    curso_svc = ambiente["curso_service"]
    hoje = date.today()

    # 1. Cadastrar Curso em Rascunho (US-01)
    req_curso = CursoCreateRequest(
        nome="Arquitetura de Software",
        descricao="Aprenda Clean Architecture e DDD na prática.",
        modalidade="gravado",
        carga_horaria=40,
        data_inicio=hoje,
        data_fim=hoje + timedelta(days=60),
        inscricao_inicio=hoje,
        inscricao_fim=hoje + timedelta(days=20),
        vagas=30,
        valor_matricula=Decimal("299.90"),
        cronograma="4 semanas intensivas",
    )
    criado = criar_curso(req=req_curso, coord=coord, service=curso_svc)
    curso_id = criado["id"]
    assert criado["status"] == "rascunho"

    # Rascunho não aparece na lista pública (US-06 c3)
    publicados_antes = listar_cursos_publicados(service=curso_svc)
    assert len(publicados_antes) == 0

    # 2. Editar Curso (US-01 c4)
    req_edit = CursoUpdateRequest(cronograma="5 semanas intensivas")
    editar_curso(curso_id=curso_id, req=req_edit, coord=coord, service=curso_svc)

    # 3. Adicionar Módulo (US-02)
    # Link inválido -> 400 Bad Request (US-02 c4)
    with pytest.raises(HTTPException) as exc_mod:
        adicionar_modulo(
            curso_id=curso_id,
            req=ModuloCreateRequest(titulo="Intro", link="link_invalido"),
            coord=coord,
            service=curso_svc,
        )
    assert exc_mod.value.status_code == status.HTTP_400_BAD_REQUEST

    # Módulo válido (US-02 c1)
    adicionar_modulo(
        curso_id=curso_id,
        req=ModuloCreateRequest(titulo="Módulo 1: Fundamentos", link="https://youtube.com/watch?v=intro"),
        coord=coord,
        service=curso_svc,
    )

    # 4. Publicar Curso (US-03)
    pub = publicar_curso(curso_id=curso_id, coord=coord, service=curso_svc)
    assert pub["status"] == "publicado"

    # 5. Listar cursos publicados (US-06 c1, c4)
    publicados = listar_cursos_publicados(service=curso_svc)
    assert len(publicados) == 1
    assert publicados[0].situacao == "inscrições abertas"
    assert publicados[0].aceita_inscricoes is True

    # 6. Ver detalhes do curso publicado SEM os links (US-06 c2)
    detalhes = obter_detalhes_curso(curso_id=curso_id, service=curso_svc)
    assert len(detalhes.modulos) == 1
    assert detalhes.modulos[0].titulo == "Módulo 1: Fundamentos"
    assert detalhes.modulos[0].link is None  # Sem link de acesso para o público!


# --- US-07, US-08, US-09: Inscrições, Pagamento e Acesso ---

def test_api_fluxo_inscricao_pagamento_e_liberacao_links(ambiente):
    coord = ambiente["coordenador"]
    auth_svc = ambiente["auth_service"]
    curso_svc = ambiente["curso_service"]
    hoje = date.today()

    aluno = auth_svc.criar_conta_aluno("Lucas Silva", "lucas@exemplo.com", "senha123")

    # Preparar curso publicado com módulo
    req_curso = CursoCreateRequest(
        nome="Engenharia de Software Moderna",
        descricao="Curso de GQS e Engenharia de Software",
        modalidade="gravado",
        carga_horaria=30,
        data_inicio=hoje,
        data_fim=hoje + timedelta(days=45),
        inscricao_inicio=hoje,
        inscricao_fim=hoje + timedelta(days=15),
        vagas=20,
        valor_matricula=Decimal("190.00"),
    )
    curso_info = criar_curso(req=req_curso, coord=coord, service=curso_svc)
    curso_id = curso_info["id"]

    adicionar_modulo(
        curso_id=curso_id,
        req=ModuloCreateRequest(titulo="Módulo Único", link="https://youtube.com/watch?v=aula1"),
        coord=coord,
        service=curso_svc,
    )
    publicar_curso(curso_id=curso_id, coord=coord, service=curso_svc)

    # 1. Aluno se inscreve (US-07 c1, c2)
    inscricao_resp = inscrever_em_curso(curso_id=curso_id, aluno=aluno, service=curso_svc)
    assert inscricao_resp.status == "aguardando_pagamento"
    assert inscricao_resp.chave_pix is not None
    assert "Chave Pix para pagamento" in inscricao_resp.instrucoes_pagamento

    # Segunda inscrição é recusada -> 409 Conflict (US-07 c3)
    with pytest.raises(HTTPException) as exc_dup:
        inscrever_em_curso(curso_id=curso_id, aluno=aluno, service=curso_svc)
    assert exc_dup.value.status_code == status.HTTP_409_CONFLICT

    # 2. Aluno vê curso em "Meus Cursos" ainda pendente (US-09 c1, c3)
    meus_cursos = listar_meus_cursos(aluno=aluno, service=curso_svc)
    assert len(meus_cursos) == 1
    assert meus_cursos[0].status_inscricao == "aguardando_pagamento"
    assert meus_cursos[0].acesso_liberado is False

    detalhe_pendente = obter_meu_curso(curso_id=curso_id, aluno=aluno, service=curso_svc)
    assert detalhe_pendente.acesso_liberado is False
    assert detalhe_pendente.modulos[0].link is None  # Sem link antes de pagar
    assert detalhe_pendente.instrucoes_pagamento is not None

    # 3. Coordenador lista inscritos (US-08 c1)
    inscritos = listar_inscritos(curso_id=curso_id, coord=coord, service=curso_svc)
    assert len(inscritos) == 1
    assert inscritos[0].email == "lucas@exemplo.com"
    assert inscritos[0].status == "aguardando_pagamento"

    # 4. Coordenador confirma pagamento (US-08 c2, c4)
    confirmacao = confirmar_pagamento(
        curso_id=curso_id,
        aluno_email="lucas@exemplo.com",
        coord=coord,
        service=curso_svc,
    )
    assert confirmacao.status == "pagamento_confirmado"
    assert confirmacao.acesso_enviado_em is not None
    assert confirmacao.modulos_liberados_total == 1

    # Segunda confirmação é recusada (US-08 c3) -> 400 Bad Request
    with pytest.raises(HTTPException) as exc_conf2:
        confirmar_pagamento(
            curso_id=curso_id,
            aluno_email="lucas@exemplo.com",
            coord=coord,
            service=curso_svc,
        )
    assert exc_conf2.value.status_code == status.HTTP_400_BAD_REQUEST

    # 5. Aluno agora vê os links de acesso liberados (US-09 c2, c4)
    detalhe_liberado = obter_meu_curso(curso_id=curso_id, aluno=aluno, service=curso_svc)
    assert detalhe_liberado.acesso_liberado is True
    assert detalhe_liberado.modulos[0].link == "https://youtube.com/watch?v=aula1"
