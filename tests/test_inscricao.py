"""Testes para Inscricao (Entidade).

Rastreabilidade: US-08, US-09
"""

from datetime import datetime, date

import pytest

from domain.inscricao import Inscricao
from domain.curso import Curso
from domain.usuario import Usuario
from domain.periodo import Periodo
from domain.modulo import Modulo
from domain.enums import Modalidade, StatusCurso, StatusInscricao, Perfil
from domain.exceptions import InscricaoInvalida, PagamentoJaConfirmado


def _curso_publicado(**overrides) -> Curso:
    """Factory para curso publicado."""
    defaults = dict(
        nome="Python Básico",
        descricao="Curso introdutório",
        modalidade=Modalidade.GRAVADO,
        carga_horaria=20,
        datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)),
        periodo_inscricao=Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 30)),
        vagas=30,
        valor_matricula=299.90,
        status=StatusCurso.PUBLICADO,
    )
    defaults.update(overrides)
    return Curso(**defaults)


def _aluno() -> Usuario:
    return Usuario(nome="João", email="joao@email.com", senha_hash="hash123", perfil=Perfil.ALUNO)


def _coordenador() -> Usuario:
    return Usuario(nome="Maria", email="maria@email.com", senha_hash="hash123", perfil=Perfil.COORDENADOR)


class TestInscricaoCriacao:
    """Testes de criação da Inscrição."""

    def test_inscricao_criada_com_status_aguardando_pagamento(self):
        """Inscrição nasce com status AGUARDANDO_PAGAMENTO."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        assert inscricao.status == StatusInscricao.AGUARDANDO_PAGAMENTO

    def test_inscricao_acesso_enviado_em_inicia_none(self):
        """acesso_enviado_em inicia como None."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        assert inscricao.acesso_enviado_em is None

    def test_inscricao_apenas_aluno(self):
        """Só alunos podem se inscrever (perfil ALUNO)."""
        curso = _curso_publicado()
        coordenador = _coordenador()
        with pytest.raises(InscricaoInvalida) as exc:
            Inscricao(aluno=coordenador, curso=curso, data=datetime.now())
        assert "aluno" in str(exc.value).lower()

    def test_inscricao_apenas_curso_publicado(self):
        """Só cursos publicados podem receber inscrição."""
        curso = _curso_publicado(status=StatusCurso.RASCUNHO)
        aluno = _aluno()
        with pytest.raises(InscricaoInvalida) as exc:
            Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        assert "publicado" in str(exc.value).lower()


class TestInscricaoConfirmacaoPagamento:
    """Testes de confirmação de pagamento (US-08)."""

    # US-08 c2: Confirmar muda o status para pagamento confirmado
    def test_us08_c2_confirmar_pagamento_muda_status(self):
        """US-08 c2: confirmar_pagamento() muda status para PAGAMENTO_CONFIRMADO."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()
        assert inscricao.status == StatusInscricao.PAGAMENTO_CONFIRMADO

    # US-08 c3: Não confirma duas vezes
    def test_us08_c3_confirmar_pagamento_duas_vezes_lanca(self):
        """US-08 c3: Confirmar pagamento duas vezes lança PagamentoJaConfirmado."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()
        with pytest.raises(PagamentoJaConfirmado) as exc:
            inscricao.confirmar_pagamento()
        assert "já foi confirmado" in str(exc.value)


class TestInscricaoEnvioAcesso:
    """Testes de registro de envio de acesso (US-08 c4)."""

    # US-08 c4: Registra se e quando o e-mail de acesso saiu
    def test_us08_c4_registrar_envio_acesso_sucesso(self):
        """US-08 c4: registrar_envio_acesso() registra a data/hora."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()
        quando = datetime(2025, 6, 20, 10, 30)
        inscricao.registrar_envio_acesso(quando)
        assert inscricao.acesso_enviado_em == quando

    def test_us08_c4_registrar_envio_acesso_sem_confirmacao_lanca(self):
        """US-08 c4: Registrar envio sem confirmação lança InscricaoInvalida."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        # Sem confirmar pagamento
        with pytest.raises(InscricaoInvalida) as exc:
            inscricao.registrar_envio_acesso(datetime.now())
        assert "confirmação" in str(exc.value).lower()


class TestInscricaoAcessoLiberado:
    """Testes de acesso liberado e links (US-08 c2, US-09 c2, c3, c4)."""

    # US-08 c2 · US-09 c2 · US-09 c3: Links só depois da confirmação
    def test_us08_c2_us09_c2_us09_c3_acesso_liberado_false_aguardando(self):
        """US-08 c2 · US-09 c2 · US-09 c3: acesso_liberado() é False enquanto aguardando pagamento."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        assert inscricao.acesso_liberado() is False

    def test_us08_c2_us09_c2_us09_c3_acesso_liberado_true_confirmado(self):
        """US-08 c2 · US-09 c2 · US-09 c3: acesso_liberado() é True após confirmação."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()
        assert inscricao.acesso_liberado() is True

    def test_us08_c2_us09_c2_us09_c3_links_liberados_vazio_aguardando(self):
        """US-08 c2 · US-09 c2 · US-09 c3: links_liberados() retorna lista vazia enquanto aguardando."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        assert inscricao.links_liberados() == []

    def test_us08_c2_us09_c2_us09_c3_links_liberados_retorna_modulos_confirmado(self):
        """US-08 c2 · US-09 c2 · US-09 c3: links_liberados() retorna módulos após confirmação."""
        curso = _curso_publicado()
        modulo1 = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        modulo2 = Modulo(titulo="Módulo 2", link="https://youtube.com/v2")
        curso.adicionar_modulo(modulo1)
        curso.adicionar_modulo(modulo2)

        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()

        links = inscricao.links_liberados()
        assert len(links) == 2
        assert links[0].titulo == "Módulo 1"
        assert links[1].titulo == "Módulo 2"

    # US-09 c4: Links sempre atualizados (lê do curso na hora)
    def test_us09_c4_links_liberados_sempre_atualizados(self):
        """US-09 c4: links_liberados() lê módulos do curso na hora (não guarda cópia)."""
        curso = _curso_publicado()
        aluno = _aluno()
        inscricao = Inscricao(aluno=aluno, curso=curso, data=datetime.now())
        inscricao.confirmar_pagamento()

        # Adiciona módulo DEPOIS da confirmação
        modulo1 = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        curso.adicionar_modulo(modulo1)

        links = inscricao.links_liberados()
        assert len(links) == 1
        assert links[0].titulo == "Módulo 1"

        # Adiciona mais um
        modulo2 = Modulo(titulo="Módulo 2", link="https://youtube.com/v2")
        curso.adicionar_modulo(modulo2)

        links = inscricao.links_liberados()
        assert len(links) == 2
        assert links[1].titulo == "Módulo 2"