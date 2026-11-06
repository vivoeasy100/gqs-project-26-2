"""Entidade: Inscricao (Passo 2 e 3).

Regras:
- US-08 c2: Confirmar muda o status para pagamento confirmado (confirmar_pagamento)
- US-08 c3: Não confirma duas vezes (confirmar_pagamento)
- US-08 c4: Registra se e quando o e-mail de acesso saiu (registrar_envio_acesso)
- US-08 c2 · US-09 c2 · US-09 c3: Links só depois da confirmação (acesso_liberado, links_liberados)
- US-09 c4: Links sempre atualizados (links_liberados lê os módulos do curso na hora)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from .enums import StatusInscricao
from .curso import Curso
from .usuario import Usuario
from .exceptions import InscricaoInvalida, PagamentoJaConfirmado
from .modulo import Modulo

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class Inscricao:
    """Inscrição de um aluno em um curso."""

    aluno: Usuario
    curso: Curso
    data: datetime
    status: StatusInscricao = StatusInscricao.AGUARDANDO_PAGAMENTO
    acesso_enviado_em: datetime | None = None

    def __post_init__(self) -> None:
        if self.aluno.perfil.value != "aluno":
            raise InscricaoInvalida("Só alunos podem se inscrever")
        if self.curso.status.value != "publicado":
            raise InscricaoInvalida("Só é possível inscrever em cursos publicados")

    # --- US-08 ---

    def confirmar_pagamento(self) -> None:
        """US-08 c2, c3: Confirmar muda status para pagamento confirmado; não confirma duas vezes."""
        if self.status == StatusInscricao.PAGAMENTO_CONFIRMADO:
            raise PagamentoJaConfirmado("Pagamento já foi confirmado")
        self.status = StatusInscricao.PAGAMENTO_CONFIRMADO

    def registrar_envio_acesso(self, quando: datetime) -> None:
        """US-08 c4: Registra se e quando o e-mail de acesso saiu."""
        if self.status != StatusInscricao.PAGAMENTO_CONFIRMADO:
            raise InscricaoInvalida("Só pode registrar envio após confirmação de pagamento")
        self.acesso_enviado_em = quando

    def acesso_liberado(self) -> bool:
        """US-08 c2 · US-09 c2 · US-09 c3: Links só depois da confirmação."""
        return self.status == StatusInscricao.PAGAMENTO_CONFIRMADO

    def links_liberados(self) -> list[Modulo]:
        """US-09 c2, c3, c4: Links liberados (lê os módulos do curso na hora - sempre atualizados)."""
        if not self.acesso_liberado():
            return []
        # US-09 c4: não guarda cópia, lê do curso na hora
        return list(self.curso.modulos)