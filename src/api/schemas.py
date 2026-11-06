"""Schemas Pydantic para validação e serialização da API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class UsuarioCadastroRequest(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome completo do aluno")
    email: str = Field(..., min_length=3, description="E-mail único")
    senha: str = Field(..., min_length=1, description="Senha de acesso")


class UsuarioLoginRequest(BaseModel):
    email: str = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., description="Senha")


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    email: str
    perfil: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class CursoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    descricao: str = Field(..., min_length=1)
    modalidade: str = Field(..., description="'gravado' ou 'sincrono'")
    carga_horaria: int = Field(..., gt=0)
    data_inicio: date
    data_fim: date
    inscricao_inicio: date
    inscricao_fim: date
    vagas: int = Field(..., gt=0)
    valor_matricula: Decimal = Field(..., ge=0)
    cronograma: str = ""


class CursoUpdateRequest(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    carga_horaria: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    inscricao_inicio: date | None = None
    inscricao_fim: date | None = None
    vagas: int | None = None
    valor_matricula: Decimal | None = None
    cronograma: str | None = None


class ModuloCreateRequest(BaseModel):
    titulo: str = Field(..., min_length=1)
    link: str = Field(..., min_length=1, description="URL do Meet ou YouTube")
    data: date | None = None


class ModuloResponse(BaseModel):
    titulo: str
    data: date | None = None
    link: str | None = None


class CursoResumoResponse(BaseModel):
    id: int
    nome: str
    modalidade: str
    carga_horaria: int
    data_inicio: date
    data_fim: date
    periodo_inscricao_inicio: date
    periodo_inscricao_fim: date
    vagas: int
    vagas_ocupadas: int
    valor_matricula: Decimal
    situacao: str
    aceita_inscricoes: bool


class CursoDetalheResponse(CursoResumoResponse):
    descricao: str
    cronograma: str
    modulos: list[ModuloResponse]


class InscricaoResponse(BaseModel):
    curso_id: int
    curso_nome: str
    aluno_nome: str
    aluno_email: str
    status: str
    valor_matricula: Decimal
    chave_pix: str
    instrucoes_pagamento: str


class InscritoItemResponse(BaseModel):
    nome: str
    email: str
    data: datetime
    status: str
    acesso_enviado_em: datetime | None = None


class ConfirmacaoPagamentoResponse(BaseModel):
    curso_id: int
    aluno_email: str
    status: str
    acesso_enviado_em: datetime | None
    modulos_liberados_total: int


class MeuCursoItemResponse(BaseModel):
    curso_id: int
    curso_nome: str
    modalidade: str
    status_inscricao: str
    acesso_liberado: bool
    data_inscricao: datetime


class MeuCursoDetalheResponse(BaseModel):
    curso_id: int
    curso_nome: str
    descricao: str
    modalidade: str
    status_inscricao: str
    acesso_liberado: bool
    modulos: list[ModuloResponse]
    instrucoes_pagamento: str | None = None

