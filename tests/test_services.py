"""Testes de unidade e integração dos Serviços de Aplicação."""

from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest

from domain.enums import Modalidade, Perfil, StatusCurso, StatusInscricao
from domain.exceptions import (
    CursoInvalido,
    InscricaoDuplicada,
    InscricaoInvalida,
    PagamentoJaConfirmado,
    UsuarioInvalido,
)
from domain.usuario import Usuario
from repositories.curso_repository import CursoRepository
from repositories.usuario_repository import UsuarioRepository
from services.auth_service import AuthService, CredenciaisInvalidas, EmailJaCadastrado
from services.curso_service import (
    AcessoNegadoError,
    CursoNaoEncontradoError,
    CursoService,
    InscricaoNaoEncontradaError,
)
from services.email_service import EmailService


@pytest.fixture
def repos():
    u_repo = UsuarioRepository()
    c_repo = CursoRepository()
    e_svc = EmailService()
    auth_svc = AuthService(u_repo)
    curso_svc = CursoService(c_repo, e_svc)
    return {
        "usuario_repo": u_repo,
        "curso_repo": c_repo,
        "email_service": e_svc,
        "auth_service": auth_svc,
        "curso_service": curso_svc,
    }


@pytest.fixture
def coordenador(repos):
    return repos["auth_service"].cadastrar_coordenador_inicial(
        nome="Coord Teste",
        email="coord@teste.com",
        senha="senha_coordenador_123",
    )


@pytest.fixture
def aluno(repos):
    return repos["auth_service"].criar_conta_aluno(
        nome="Aluno Teste",
        email="aluno@teste.com",
        senha="senha_aluno_123",
    )


def test_auth_service_criar_conta_sucesso(repos):
    auth_svc = repos["auth_service"]
    user = auth_svc.criar_conta_aluno("Maria Silva", "maria@teste.com", "senha123")
    assert user.nome == "Maria Silva"
    assert user.email == "maria@teste.com"
    assert user.perfil == Perfil.ALUNO


def test_auth_service_criar_conta_email_duplicado(repos, aluno):
    auth_svc = repos["auth_service"]
    with pytest.raises(EmailJaCadastrado):
        auth_svc.criar_conta_aluno("Outro Aluno", aluno.email, "outrasenha")


def test_auth_service_criar_conta_invalido(repos):
    auth_svc = repos["auth_service"]
    with pytest.raises(UsuarioInvalido):
        auth_svc.criar_conta_aluno("", "invalido@teste.com", "senha")
    with pytest.raises(UsuarioInvalido):
        auth_svc.criar_conta_aluno("Nome", "sem_arroba", "senha")


def test_auth_service_login_sucesso_e_logout(repos, aluno):
    auth_svc = repos["auth_service"]
    user, token = auth_svc.login("aluno@teste.com", "senha_aluno_123")
    assert user.email == aluno.email
    assert auth_svc.obter_usuario_por_token(token) == user

    # Logout
    assert auth_svc.logout(token) is True
    assert auth_svc.obter_usuario_por_token(token) is None


def test_auth_service_login_falha_mensagem_generica(repos):
    auth_svc = repos["auth_service"]
    with pytest.raises(CredenciaisInvalidas, match="E-mail ou senha incorretos"):
        auth_svc.login("inexistente@teste.com", "123456")


def test_curso_service_cadastrar_curso_exige_coordenador(repos, aluno):
    curso_svc = repos["curso_service"]
    hoje = date.today()
    with pytest.raises(AcessoNegadoError):
        curso_svc.cadastrar_curso(
            nome="Python Básico",
            descricao="Intro",
            modalidade=Modalidade.GRAVADO,
            carga_horaria=20,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
            inscricao_inicio=hoje,
            inscricao_fim=hoje + timedelta(days=10),
            vagas=50,
            valor_matricula=Decimal("150.00"),
            usuario_autor=aluno,
        )


def test_curso_service_fluxo_completo(repos, coordenador, aluno):
    curso_svc = repos["curso_service"]
    email_svc = repos["email_service"]
    hoje = date.today()

    # 1. Cadastrar curso (US-01)
    cid, curso = curso_svc.cadastrar_curso(
        nome="Curso FastAPI Avançado",
        descricao="Domínio e API",
        modalidade=Modalidade.GRAVADO,
        carga_horaria=40,
        data_inicio=hoje,
        data_fim=hoje + timedelta(days=60),
        inscricao_inicio=hoje,
        inscricao_fim=hoje + timedelta(days=15),
        vagas=30,
        valor_matricula=Decimal("250.00"),
        usuario_autor=coordenador,
    )
    assert curso.status == StatusCurso.RASCUNHO

    # 2. Adicionar módulo (US-02)
    curso_svc.adicionar_modulo(
        curso_id=cid,
        titulo="Módulo 1 - Arquitetura",
        link="https://youtube.com/watch?v=modulo1",
        usuario_autor=coordenador,
    )
    assert len(curso.modulos) == 1

    # 3. Publicar curso (US-03)
    curso_svc.publicar_curso(cid, usuario_autor=coordenador)
    assert curso.status == StatusCurso.PUBLICADO

    # 4. Ver curso na lista pública (US-06)
    cursos_publicos = curso_svc.listar_cursos_publicados(hoje=hoje)
    assert len(cursos_publicos) == 1
    assert cursos_publicos[0]["situacao"] == "inscrições abertas"

    # Detalhes sem link (US-06 c2)
    detalhes = curso_svc.obter_detalhes_curso(cid, hoje=hoje)
    assert "link" not in detalhes["modulos"][0] or detalhes["modulos"][0].get("link") is None

    # 5. Inscrever aluno (US-07)
    res_inscricao = curso_svc.inscrever_aluno(cid, aluno, hoje=hoje)
    assert res_inscricao["status"] == "aguardando_pagamento"
    assert "chave_pix" in res_inscricao

    # E-mail de pagamento recebido
    emails_aluno = email_svc.obter_emails_por_destinatario(aluno.email)
    assert len(emails_aluno) == 1
    assert emails_aluno[0].tipo == "instrucoes_pagamento"

    # Não permite inscrição duplicada
    with pytest.raises(InscricaoDuplicada):
        curso_svc.inscrever_aluno(cid, aluno, hoje=hoje)

    # 6. Aluno visualiza "Meus Cursos" ainda pendente (US-09 c3)
    meu_curso = curso_svc.obter_meu_curso_detalhe(cid, aluno)
    assert meu_curso["acesso_liberado"] is False
    assert "instrucoes_pagamento" in meu_curso
    assert "link" not in meu_curso["modulos"][0]

    # 7. Coordenador lista inscritos e confirma pagamento (US-08)
    inscritos = curso_svc.listar_inscritos(cid, usuario_autor=coordenador)
    assert len(inscritos) == 1
    assert inscritos[0]["status"] == "aguardando_pagamento"

    agora = datetime(2026, 11, 5, 20, 0, 0)
    confirmacao = curso_svc.confirmar_pagamento(
        cid, aluno.email, usuario_autor=coordenador, agora=agora
    )
    assert confirmacao["status"] == "pagamento_confirmado"
    assert confirmacao["acesso_enviado_em"] == agora

    # Não confirma duas vezes
    with pytest.raises(PagamentoJaConfirmado):
        curso_svc.confirmar_pagamento(cid, aluno.email, usuario_autor=coordenador)

    # E-mail de links de acesso enviado
    emails_aluno = email_svc.obter_emails_por_destinatario(aluno.email)
    assert len(emails_aluno) == 2
    assert emails_aluno[1].tipo == "links_acesso"
    assert "https://youtube.com/watch?v=modulo1" in emails_aluno[1].conteudo

    # 8. Aluno acessa novamente e vê os links liberados (US-09 c2, c4)
    meu_curso_liberado = curso_svc.obter_meu_curso_detalhe(cid, aluno)
    assert meu_curso_liberado["acesso_liberado"] is True
    assert meu_curso_liberado["modulos"][0]["link"] == "https://youtube.com/watch?v=modulo1"

