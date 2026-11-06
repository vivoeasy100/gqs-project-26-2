"""Rotas de Inscrições e Área do Aluno (US-07, US-08, US-09)."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_curso_service,
    require_aluno,
    require_coordenador,
)
from api.schemas import (
    ConfirmacaoPagamentoResponse,
    InscricaoResponse,
    InscritoItemResponse,
    MeuCursoDetalheResponse,
    MeuCursoItemResponse,
)
from domain.exceptions import (
    CursoNaoPublicado,
    ForaDoPeriodoInscricao,
    InscricaoDuplicada,
    InscricaoInvalida,
    PagamentoJaConfirmado,
    VagasEsgotadas,
)
from domain.usuario import Usuario
from services.curso_service import (
    CursoNaoEncontradoError,
    CursoService,
    InscricaoNaoEncontradaError,
)

router = APIRouter(tags=["Inscrições"])


@router.post(
    "/cursos/{curso_id}/inscrever",
    response_model=InscricaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="US-07: Inscrever-se em um curso (Aluno)",
)
def inscrever_em_curso(
    curso_id: int,
    aluno: Usuario = Depends(require_aluno),
    service: CursoService = Depends(get_curso_service),
) -> InscricaoResponse:
    """US-07: Cria inscrição em status aguardando pagamento e envia instruções Pix por e-mail."""
    try:
        dados = service.inscrever_aluno(curso_id=curso_id, aluno=aluno)
        return InscricaoResponse(**dados)
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InscricaoDuplicada as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (CursoNaoPublicado, ForaDoPeriodoInscricao, VagasEsgotadas, InscricaoInvalida) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/cursos/{curso_id}/inscritos",
    response_model=list[InscritoItemResponse],
    summary="US-08 c1: Ver lista de inscritos do curso (Coordenador)",
)
def listar_inscritos(
    curso_id: int,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> list[InscritoItemResponse]:
    """US-08 c1: Lista nome, e-mail, data e status dos inscritos no curso."""
    try:
        inscritos = service.listar_inscritos(curso_id=curso_id, usuario_autor=coord)
        return [InscritoItemResponse(**item) for item in inscritos]
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/cursos/{curso_id}/inscricoes/{aluno_email}/confirmar",
    response_model=ConfirmacaoPagamentoResponse,
    summary="US-08 c2-c4: Confirmar pagamento de inscrição (Coordenador)",
)
def confirmar_pagamento(
    curso_id: int,
    aluno_email: str,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> ConfirmacaoPagamentoResponse:
    """US-08 c2, c3, c4: Confirma o pagamento, envia os links por e-mail e registra a data/hora do envio."""
    try:
        resp = service.confirmar_pagamento(
            curso_id=curso_id,
            aluno_email=aluno_email,
            usuario_autor=coord,
        )
        return ConfirmacaoPagamentoResponse(**resp)
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InscricaoNaoEncontradaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PagamentoJaConfirmado as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/meus-cursos",
    response_model=list[MeuCursoItemResponse],
    summary="US-09 c1: Ver meus cursos inscritos (Aluno)",
)
def listar_meus_cursos(
    aluno: Usuario = Depends(require_aluno),
    service: CursoService = Depends(get_curso_service),
) -> list[MeuCursoItemResponse]:
    """US-09 c1: Lista os cursos em que o aluno logado está inscrito."""
    return [MeuCursoItemResponse(**item) for item in service.listar_meus_cursos(aluno)]


@router.get(
    "/meus-cursos/{curso_id}",
    response_model=MeuCursoDetalheResponse,
    summary="US-09 c2-c4: Ver detalhes e links do meu curso (Aluno)",
)
def obter_meu_curso(
    curso_id: int,
    aluno: Usuario = Depends(require_aluno),
    service: CursoService = Depends(get_curso_service),
) -> MeuCursoDetalheResponse:
    """US-09 c2-c4: Se pagamento confirmado, mostra os links atualizados; se pendente, mostra instruções sem link."""
    try:
        dados = service.obter_meu_curso_detalhe(curso_id=curso_id, aluno=aluno)
        return MeuCursoDetalheResponse(**dados)
    except (CursoNaoEncontradoError, InscricaoNaoEncontradaError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

