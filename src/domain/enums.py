"""Enums do domínio (Passo 2)."""

from enum import Enum


class Modalidade(Enum):
    """Modalidade do curso."""
    GRAVADO = "gravado"
    SINCRONO = "sincrono"


class StatusCurso(Enum):
    """Status do curso."""
    RASCUNHO = "rascunho"
    PUBLICADO = "publicado"


class StatusInscricao(Enum):
    """Status da inscrição."""
    AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
    PAGAMENTO_CONFIRMADO = "pagamento_confirmado"


class Perfil(Enum):
    """Perfil do usuário."""
    ALUNO = "aluno"
    COORDENADOR = "coordenador"