"""Entidade: Curso (Passo 2 e 3).

Regras implementadas:
- US-01 c1: Curso novo nasce em rascunho
- US-01 c2: Campos obrigatórios preenchidos
- US-01 c3: Período de inscrição não termina depois do fim do curso
- US-01 c5: Síncrono: vagas <= limite do Meet (a confirmar)
- US-01 c4 · US-03 c3: Editar revalida tudo (editar)
- US-02 c1: Módulo passa a fazer parte do curso (adicionar_modulo)
- US-02 c3: Síncrono: módulo com data, dentro das datas do curso (adicionar_modulo)
- US-02 c2: Editar ou remover módulo (remover_modulo)
- US-03 c1: Só publica o que está em rascunho e válido (publicar)
- US-03 c2 · US-07 c4: Aceita inscrição: publicado, dentro do período e com vaga (aceita_inscricoes)
- US-07 c5: Quantas vagas estão ocupadas (vagas_ocupadas)
- US-06 c4: Situação: "inscrições abertas", "inscrições encerradas" ou "esgotado" (situacao)
- US-06 c3: Rascunho nunca aparece para o aluno (visivel_para_aluno)
- US-07 c1: Inscrição nasce aguardando pagamento (inscrever)
- US-07 c3: Aluno já inscrito não gera segunda inscrição (inscrever)
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from .enums import Modalidade, StatusCurso, StatusInscricao
from .exceptions import (
    CursoInvalido,
    CursoNaoPublicado,
    ForaDoPeriodoInscricao,
    InscricaoDuplicada,
    VagasEsgotadas,
)
from .modulo import Modulo
from .periodo import Periodo
from .usuario import Usuario

if TYPE_CHECKING:
    from .inscricao import Inscricao


@dataclass(slots=True)
class Curso:
    """Curso online."""

    nome: str
    descricao: str
    modalidade: Modalidade
    carga_horaria: int
    datas: Periodo
    periodo_inscricao: Periodo
    vagas: int
    valor_matricula: Decimal
    cronograma: str = ""
    status: StatusCurso = StatusCurso.RASCUNHO
    modulos: list[Modulo] = field(default_factory=list)
    inscricoes: list["Inscricao"] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validar_campos_obrigatorios()
        self._validar_periodo_inscricao()
        self._validar_vagas_sincrono()

    # --- US-01 c1, c2, c3, c5 ---

    def _validar_campos_obrigatorios(self) -> None:
        """US-01 c2: Campos obrigatórios preenchidos."""
        if not self.nome.strip():
            raise CursoInvalido("Nome é obrigatório")
        if not self.descricao.strip():
            raise CursoInvalido("Descrição é obrigatória")
        if self.carga_horaria <= 0:
            raise CursoInvalido("Carga horária deve ser positiva")
        if self.vagas <= 0:
            raise CursoInvalido("Vagas deve ser positivo")
        if self.valor_matricula < 0:
            raise CursoInvalido("Valor da matrícula não pode ser negativo")

    def _validar_periodo_inscricao(self) -> None:
        """US-01 c3: Período de inscrição não termina depois do fim do curso."""
        if self.periodo_inscricao.fim > self.datas.fim:
            raise CursoInvalido(
                f"Período de inscrição ({self.periodo_inscricao.fim}) "
                f"não pode terminar depois do fim do curso ({self.datas.fim})"
            )

    def _validar_vagas_sincrono(self) -> None:
        """US-01 c5: Síncrono: vagas <= limite do Meet (a confirmar: limite)."""
        if self.modalidade == Modalidade.SINCRONO:
            # Limite do Meet a confirmar - usando 100 como placeholder
            LIMITE_MEET = 100
            if self.vagas > LIMITE_MEET:
                raise CursoInvalido(
                    f"Curso síncrono: vagas ({self.vagas}) excedem limite do Meet ({LIMITE_MEET})"
                )

    # --- US-01 c4 · US-03 c3 ---

    def editar(
        self,
        *,
        nome: str | None = None,
        descricao: str | None = None,
        cronograma: str | None = None,
        carga_horaria: int | None = None,
        vagas: int | None = None,
        valor_matricula: Decimal | None = None,
        datas: Periodo | None = None,
        periodo_inscricao: Periodo | None = None,
    ) -> None:
        """US-01 c4 · US-03 c3: Editar revalida tudo (a confirmar: o que pode mudar depois de publicado)."""
        if nome is not None:
            self.nome = nome
        if descricao is not None:
            self.descricao = descricao
        if cronograma is not None:
            self.cronograma = cronograma
        if carga_horaria is not None:
            self.carga_horaria = carga_horaria
        if vagas is not None:
            self.vagas = vagas
        if valor_matricula is not None:
            self.valor_matricula = valor_matricula
        if datas is not None:
            self.datas = datas
        if periodo_inscricao is not None:
            self.periodo_inscricao = periodo_inscricao

        # Revalidar
        self._validar_campos_obrigatorios()
        self._validar_periodo_inscricao()
        self._validar_vagas_sincrono()

    # --- US-02 ---

    def adicionar_modulo(self, modulo: Modulo) -> None:
        """US-02 c1, c3: Módulo passa a fazer parte do curso.
        Síncrono: módulo com data, dentro das datas do curso.
        """
        if self.modalidade == Modalidade.SINCRONO:
            if modulo.data is None:
                raise CursoInvalido("Curso síncrono exige data no módulo")
            if not self.datas.contem(modulo.data):
                raise CursoInvalido(
                    f"Data do módulo ({modulo.data}) fora das datas do curso ({self.datas})"
                )
        self.modulos.append(modulo)

    def remover_modulo(self, modulo: Modulo) -> None:
        """US-02 c2: Remover módulo."""
        if modulo in self.modulos:
            self.modulos.remove(modulo)

    # --- US-03 ---

    def publicar(self) -> None:
        """US-03 c1: Só publica o que está em rascunho e válido.
        US-03 c4: (a confirmar) Pode publicar sem módulo?
        """
        if self.status != StatusCurso.RASCUNHO:
            raise CursoInvalido("Só é possível publicar curso em rascunho")

        # Validações de publicação
        if not self.modulos:
            # US-03 c4 × RN-01.3: a confirmar se pode publicar sem módulo
            # Por enquanto permite (segue US-03 c4)
            pass

        self.status = StatusCurso.PUBLICADO

    def visivel_para_aluno(self) -> bool:
        """US-06 c3: Rascunho nunca aparece para o aluno."""
        return self.status == StatusCurso.PUBLICADO

    def aceita_inscricoes(self, hoje: date) -> bool:
        """US-03 c2 · US-07 c4: Aceita inscrição: publicado, dentro do período e com vaga."""
        if self.status != StatusCurso.PUBLICADO:
            return False
        if not self.periodo_inscricao.contem(hoje):
            return False
        if self.vagas_ocupadas() >= self.vagas:
            return False
        return True

    def vagas_ocupadas(self) -> int:
        """US-07 c5: Quantas vagas estão ocupadas (a confirmar: conta na inscrição ou só na confirmação?).
        Por enquanto: conta inscrições com pagamento confirmado.
        """
        return sum(1 for i in self.inscricoes if i.status == StatusInscricao.PAGAMENTO_CONFIRMADO)

    def situacao(self, hoje: date) -> str:
        """US-06 c4: "inscrições abertas", "inscrições encerradas" ou "esgotado"."""
        if self.status != StatusCurso.PUBLICADO:
            return "rascunho"
        if not self.periodo_inscricao.contem(hoje):
            if hoje < self.periodo_inscricao.inicio:
                return "inscrições ainda não abertas"
            return "inscrições encerradas"
        if self.vagas_ocupadas() >= self.vagas:
            return "esgotado"
        return "inscrições abertas"

    # --- US-07 ---

    def inscrever(self, aluno: Usuario, hoje: date) -> "Inscricao":
        """US-07 c1, c3: Inscrição nasce aguardando pagamento; aluno já inscrito não gera segunda."""
        if not self.aceita_inscricoes(hoje):
            if self.status != StatusCurso.PUBLICADO:
                raise CursoNaoPublicado("Curso não está publicado")
            if not self.periodo_inscricao.contem(hoje):
                raise ForaDoPeriodoInscricao("Fora do período de inscrição")
            raise VagasEsgotadas("Vagas esgotadas")

        # US-07 c3: Aluno já inscrito não gera segunda inscrição
        for insc in self.inscricoes:
            if insc.aluno.email == aluno.email:
                raise InscricaoDuplicada(f"Aluno {aluno.email} já inscrito neste curso")

        from .inscricao import Inscricao

        inscricao = Inscricao(aluno=aluno, curso=self, data=datetime.now())
        self.inscricoes.append(inscricao)
        return inscricao