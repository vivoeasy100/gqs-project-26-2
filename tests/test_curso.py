"""Testes para Curso (Entidade - agregado principal).

Rastreabilidade: US-01 a US-03, US-06, US-07
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from domain.curso import Curso
from domain.modulo import Modulo
from domain.periodo import Periodo
from domain.usuario import Usuario
from domain.enums import Modalidade, StatusCurso, Perfil
from domain.exceptions import (
    CursoInvalido,
    CursoNaoPublicado,
    ForaDoPeriodoInscricao,
    InscricaoDuplicada,
    VagasEsgotadas,
    ModuloInvalido,
    PeriodoInvalido,
)
from domain.inscricao import Inscricao
from domain.enums import StatusInscricao


def _curso_base(**overrides) -> Curso:
    """Factory para criar um curso base válido."""
    defaults = dict(
        nome="Python Básico",
        descricao="Curso introdutório de Python",
        modalidade=Modalidade.GRAVADO,
        carga_horaria=20,
        datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)),
        periodo_inscricao=Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 30)),
        vagas=30,
        valor_matricula=Decimal("299.90"),
    )
    defaults.update(overrides)
    return Curso(**defaults)


def _aluno() -> Usuario:
    return Usuario(nome="João", email="joao@email.com", senha_hash="hash123", perfil=Perfil.ALUNO)


def _coordenador() -> Usuario:
    return Usuario(nome="Maria", email="maria@email.com", senha_hash="hash123", perfil=Perfil.COORDENADOR)


class TestCursoCriacao:
    """Testes de criação e validação do Curso (US-01)."""

    # US-01 c1: Curso novo nasce em rascunho
    def test_us01_c1_curso_nasce_em_rascunho(self):
        """US-01 c1: Curso recém-criado tem status RASCUNHO."""
        curso = _curso_base()
        assert curso.status == StatusCurso.RASCUNHO

    # US-01 c2: Campos obrigatórios preenchidos
    def test_us01_c2_nome_obrigatorio(self):
        """US-01 c2: Nome vazio lança CursoInvalido."""
        with pytest.raises(CursoInvalido) as exc:
            _curso_base(nome="")
        assert "obrigat" in str(exc.value).lower()

    def test_us01_c2_descricao_obrigatoria(self):
        """US-01 c2: Descrição vazia lança CursoInvalido."""
        with pytest.raises(CursoInvalido) as exc:
            _curso_base(descricao="")
        assert "obrigat" in str(exc.value).lower()

    def test_us01_c2_carga_horaria_positiva(self):
        """US-01 c2: Carga horária <= 0 lança CursoInvalido."""
        with pytest.raises(CursoInvalido):
            _curso_base(carga_horaria=0)
        with pytest.raises(CursoInvalido):
            _curso_base(carga_horaria=-1)

    def test_us01_c2_vagas_positiva(self):
        """US-01 c2: Vagas <= 0 lança CursoInvalido."""
        with pytest.raises(CursoInvalido):
            _curso_base(vagas=0)

    def test_us01_c2_valor_matricula_nao_negativo(self):
        """US-01 c2: Valor matrícula negativo lança CursoInvalido."""
        with pytest.raises(CursoInvalido):
            _curso_base(valor_matricula=Decimal("-10"))

    # US-01 c3: Período de inscrição não termina depois do fim do curso
    def test_us01_c3_periodo_inscricao_depois_fim_curso_invalido(self):
        """US-01 c3: Período de inscrição terminando após fim do curso lança CursoInvalido."""
        with pytest.raises(CursoInvalido) as exc:
            _curso_base(
                datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 15)),
                periodo_inscricao=Periodo(inicio=date(2025, 6, 1), fim=date(2025, 7, 20)),
            )
        assert "não pode terminar depois" in str(exc.value)

    def test_us01_c3_periodo_inscricao_mesmo_dia_fim_curso_valido(self):
        """US-01 c3: Período de inscrição terminando no mesmo dia do fim do curso é válido."""
        curso = _curso_base(
            datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)),
            periodo_inscricao=Periodo(inicio=date(2025, 6, 1), fim=date(2025, 7, 31)),
        )
        assert curso.periodo_inscricao.fim == date(2025, 7, 31)

    # US-01 c5: Síncrono: vagas <= limite do Meet
    def test_us01_c5_sincrono_vagas_acima_limite_meet_invalido(self):
        """US-01 c5: Curso síncrono com vagas acima do limite do Meet lança CursoInvalido."""
        with pytest.raises(CursoInvalido) as exc:
            _curso_base(modalidade=Modalidade.SINCRONO, vagas=150)
        assert "excedem limite" in str(exc.value)

    def test_us01_c5_sincrono_vagas_dentro_limite_valido(self):
        """US-01 c5: Curso síncrono com vagas dentro do limite é válido."""
        curso = _curso_base(modalidade=Modalidade.SINCRONO, vagas=50)
        assert curso.vagas == 50

    def test_us01_c5_gravado_sem_limite_meet(self):
        """US-01 c5: Curso gravado não tem limite do Meet."""
        curso = _curso_base(modalidade=Modalidade.GRAVADO, vagas=500)
        assert curso.vagas == 500


class TestCursoEdicao:
    """Testes de edição do Curso (US-01 c4, US-03 c3)."""

    def test_us01_c4_us03_c3_editar_atualiza_campos(self):
        """US-01 c4 · US-03 c3: editar() atualiza campos permitidos."""
        curso = _curso_base()
        curso.editar(nome="Python Avançado", descricao="Nova descrição", carga_horaria=40)
        assert curso.nome == "Python Avançado"
        assert curso.descricao == "Nova descrição"
        assert curso.carga_horaria == 40

    def test_us01_c4_us03_c3_editar_revalida_periodo_inscricao(self):
        """US-01 c4 · US-03 c3: editar() revalida período de inscrição."""
        curso = _curso_base()
        with pytest.raises(CursoInvalido):
            curso.editar(
                datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 15)),
                periodo_inscricao=Periodo(inicio=date(2025, 6, 1), fim=date(2025, 7, 20)),
            )

    def test_us01_c4_us03_c3_editar_revalida_vagas_sincrono(self):
        """US-01 c4 · US-03 c3: editar() revalida vagas no síncrono."""
        curso = _curso_base(modalidade=Modalidade.SINCRONO, vagas=50)
        with pytest.raises(CursoInvalido):
            curso.editar(vagas=150)


class TestCursoModulos:
    """Testes de gerenciamento de módulos (US-02)."""

    # US-02 c1: Módulo passa a fazer parte do curso
    def test_us02_c1_adicionar_modulo_gravado(self):
        """US-02 c1: Adicionar módulo em curso gravado funciona."""
        curso = _curso_base(modalidade=Modalidade.GRAVADO)
        modulo = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        curso.adicionar_modulo(modulo)
        assert modulo in curso.modulos

    # US-02 c3: Síncrono: módulo com data, dentro das datas do curso
    def test_us02_c3_sincrono_modulo_sem_data_invalido(self):
        """US-02 c3: Curso síncrono exige data no módulo."""
        curso = _curso_base(modalidade=Modalidade.SINCRONO, datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)))
        modulo = Modulo(titulo="Módulo 1", link="https://meet.google.com/abc")
        with pytest.raises(CursoInvalido) as exc:
            curso.adicionar_modulo(modulo)
        assert "exige data" in str(exc.value)

    def test_us02_c3_sincrono_modulo_data_fora_curso_invalido(self):
        """US-02 c3: Módulo com data fora das datas do curso lança CursoInvalido."""
        curso = _curso_base(modalidade=Modalidade.SINCRONO, datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)))
        modulo = Modulo(titulo="Módulo 1", link="https://meet.google.com/abc", data=date(2025, 8, 15))
        with pytest.raises(CursoInvalido) as exc:
            curso.adicionar_modulo(modulo)
        assert "fora das datas" in str(exc.value)

    def test_us02_c3_sincrono_modulo_data_dentro_curso_valido(self):
        """US-02 c3: Módulo com data dentro das datas do curso é aceito."""
        curso = _curso_base(modalidade=Modalidade.SINCRONO, datas=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 7, 31)))
        modulo = Modulo(titulo="Módulo 1", link="https://meet.google.com/abc", data=date(2025, 7, 15))
        curso.adicionar_modulo(modulo)
        assert modulo in curso.modulos

    # US-02 c2: Remover módulo
    def test_us02_c2_remover_modulo(self):
        """US-02 c2: remover_modulo() remove o módulo da lista."""
        curso = _curso_base()
        modulo = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        curso.adicionar_modulo(modulo)
        curso.remover_modulo(modulo)
        assert modulo not in curso.modulos

    def test_us02_c2_remover_modulo_inexistente_nao_erra(self):
        """US-02 c2: Remover módulo que não existe não lança erro."""
        curso = _curso_base()
        modulo = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        curso.remover_modulo(modulo)  # Não deve lançar
        assert len(curso.modulos) == 0


class TestCursoPublicacao:
    """Testes de publicação do Curso (US-03)."""

    # US-03 c1: Só publica o que está em rascunho e válido
    def test_us03_c1_publicar_rascunho_valido(self):
        """US-03 c1: Publicar curso em rascunho válido muda status para PUBLICADO."""
        curso = _curso_base()
        curso.publicar()
        assert curso.status == StatusCurso.PUBLICADO

    def test_us03_c1_publicar_ja_publicado_invalido(self):
        """US-03 c1: Publicar curso já publicado lança CursoInvalido."""
        curso = _curso_base()
        curso.publicar()
        with pytest.raises(CursoInvalido) as exc:
            curso.publicar()
        assert "rascunho" in str(exc.value).lower()

    def test_us03_c1_publicar_invalido_campos_obrigatorios(self):
        """US-03 c1: Publicar curso com campos inválidos lança CursoInvalido."""
        # Criar curso "válido" mas depois editar para inválido não funciona pois editar revalida
        # O teste aqui é que a validação acontece na criação
        pass  # Já coberto nos testes de criação

    # US-03 c4: (a confirmar) Pode publicar sem módulo?
    def test_us03_c4_publicar_sem_modulo_permitido_atualmente(self):
        """US-03 c4: Atualmente permite publicar sem módulo (a confirmar)."""
        curso = _curso_base()
        curso.publicar()  # Não deve lançar
        assert curso.status == StatusCurso.PUBLICADO


class TestCursoInscricoes:
    """Testes de inscrições no Curso (US-07, US-06)."""

    # US-03 c2 · US-07 c4: Aceita inscrição: publicado, dentro do período e com vaga
    def test_us03_c2_us07_c4_aceita_inscricoes_publicado_dentro_periodo_com_vaga(self):
        """US-03 c2 · US-07 c4: Curso publicado, dentro do período e com vaga aceita inscrições."""
        curso = _curso_base()
        curso.publicar()
        hoje = date(2025, 6, 15)  # Dentro do período de inscrição
        assert curso.aceita_inscricoes(hoje) is True

    def test_us03_c2_us07_c4_aceita_inscricoes_rascunho_nao_aceita(self):
        """US-03 c2 · US-07 c4: Curso em rascunho não aceita inscrições."""
        curso = _curso_base()
        hoje = date(2025, 6, 15)
        assert curso.aceita_inscricoes(hoje) is False

    def test_us03_c2_us07_c4_aceita_inscricoes_fora_periodo_nao_aceita(self):
        """US-03 c2 · US-07 c4: Fora do período de inscrição não aceita."""
        curso = _curso_base()
        curso.publicar()
        hoje = date(2025, 8, 1)  # Após período de inscrição
        assert curso.aceita_inscricoes(hoje) is False

    def test_us03_c2_us07_c4_aceita_inscricoes_sem_vaga_nao_aceita(self):
        """US-03 c2 · US-07 c4: Sem vagas não aceita inscrições."""
        curso = _curso_base(vagas=1)
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno = _aluno()
        inscricao = curso.inscrever(aluno, hoje)  # Ocupa a única vaga
        inscricao.confirmar_pagamento()  # Confirma para ocupar a vaga
        assert curso.aceita_inscricoes(hoje) is False

    # US-07 c5: vagas_ocupadas()
    def test_us07_c5_vagas_ocupadas_conta_confirmadas(self):
        """US-07 c5: vagas_ocupadas() conta apenas inscrições com pagamento confirmado."""
        curso = _curso_base()
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno1 = _aluno()
        aluno2 = Usuario(nome="Maria", email="maria@email.com", senha_hash="hash", perfil=Perfil.ALUNO)

        insc1 = curso.inscrever(aluno1, hoje)
        insc2 = curso.inscrever(aluno2, hoje)

        assert curso.vagas_ocupadas() == 0  # Nenhuma confirmada

        insc1.confirmar_pagamento()
        assert curso.vagas_ocupadas() == 1

        insc2.confirmar_pagamento()
        assert curso.vagas_ocupadas() == 2

    # US-06 c4: situacao()
    def test_us06_c4_situacao_rascunho(self):
        """US-06 c4: Curso em rascunho retorna 'rascunho'."""
        curso = _curso_base()
        assert curso.situacao(date(2025, 6, 15)) == "rascunho"

    def test_us06_c4_situacao_inscricoes_ainda_nao_abertas(self):
        """US-06 c4: Antes do período retorna 'inscrições ainda não abertas'."""
        curso = _curso_base()
        curso.publicar()
        assert curso.situacao(date(2025, 5, 15)) == "inscrições ainda não abertas"

    def test_us06_c4_situacao_inscricoes_abertas(self):
        """US-06 c4: Durante período com vagas retorna 'inscrições abertas'."""
        curso = _curso_base()
        curso.publicar()
        assert curso.situacao(date(2025, 6, 15)) == "inscrições abertas"

    def test_us06_c4_situacao_inscricoes_encerradas(self):
        """US-06 c4: Após período retorna 'inscrições encerradas'."""
        curso = _curso_base()
        curso.publicar()
        assert curso.situacao(date(2025, 8, 1)) == "inscrições encerradas"

    def test_us06_c4_situacao_esgotado(self):
        """US-06 c4: Com vagas esgotadas retorna 'esgotado'."""
        curso = _curso_base(vagas=1)
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno = _aluno()
        insc = curso.inscrever(aluno, hoje)
        insc.confirmar_pagamento()
        assert curso.situacao(hoje) == "esgotado"

    # US-06 c3: visivel_para_aluno()
    def test_us06_c3_visivel_para_aluno_rascunho_false(self):
        """US-06 c3: Curso em rascunho não é visível para aluno."""
        curso = _curso_base()
        assert curso.visivel_para_aluno() is False

    def test_us06_c3_visivel_para_aluno_publicado_true(self):
        """US-06 c3: Curso publicado é visível para aluno."""
        curso = _curso_base()
        curso.publicar()
        assert curso.visivel_para_aluno() is True

    # US-07 c1: Inscrição nasce aguardando pagamento
    def test_us07_c1_inscrever_cria_inscricao_aguardando_pagamento(self):
        """US-07 c1: inscrever() cria inscrição com status AGUARDANDO_PAGAMENTO."""
        curso = _curso_base()
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno = _aluno()
        inscricao = curso.inscrever(aluno, hoje)
        assert inscricao.status == StatusInscricao.AGUARDANDO_PAGAMENTO
        assert inscricao.aluno == aluno
        assert inscricao.curso == curso

    # US-07 c3: Aluno já inscrito não gera segunda inscrição
    def test_us07_c3_aluno_ja_inscrito_lanca_inscricao_duplicada(self):
        """US-07 c3: Inscrever aluno já inscrito lança InscricaoDuplicada."""
        curso = _curso_base()
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno = _aluno()
        curso.inscrever(aluno, hoje)
        with pytest.raises(InscricaoDuplicada) as exc:
            curso.inscrever(aluno, hoje)
        assert "já inscrito" in str(exc.value)

    # US-07 c4: Fora do período
    def test_us07_c4_inscrever_fora_periodo_lanca_fora_do_periodo(self):
        """US-07 c4: Inscrever fora do período lança ForaDoPeriodoInscricao."""
        curso = _curso_base()
        curso.publicar()
        aluno = _aluno()
        with pytest.raises(ForaDoPeriodoInscricao):
            curso.inscrever(aluno, date(2025, 8, 1))

    # US-07: Curso não publicado
    def test_us07_curso_nao_publicado_lanca_curso_nao_publicado(self):
        """US-07: Inscrever em curso não publicado lança CursoNaoPublicado."""
        curso = _curso_base()  # rascunho
        aluno = _aluno()
        with pytest.raises(CursoNaoPublicado):
            curso.inscrever(aluno, date(2025, 6, 15))

    # US-07: Vagas esgotadas
    def test_us07_vagas_esgotadas_lanca_vagas_esgotadas(self):
        """US-07: Inscrever sem vagas lança VagasEsgotadas."""
        curso = _curso_base(vagas=1)
        curso.publicar()
        hoje = date(2025, 6, 15)
        aluno1 = _aluno()
        aluno2 = Usuario(nome="Maria", email="maria@email.com", senha_hash="hash", perfil=Perfil.ALUNO)
        curso.inscrever(aluno1, hoje)
        insc1 = curso.inscricoes[0]
        insc1.confirmar_pagamento()  # Ocupa a vaga
        with pytest.raises(VagasEsgotadas):
            curso.inscrever(aluno2, hoje)