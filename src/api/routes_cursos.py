"""Rotas de Cursos e Módulos (US-01, US-02, US-03, US-06)."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_curso_service,
    require_coordenador,
)
from api.schemas import (
    CursoCreateRequest,
    CursoDetalheResponse,
    CursoResumoResponse,
    CursoUpdateRequest,
    ModuloCreateRequest,
    ModuloResponse,
)
from domain.enums import Modalidade
from domain.exceptions import CursoInvalido, DominioError, ModuloInvalido, PeriodoInvalido
from domain.usuario import Usuario
from services.curso_service import CursoNaoEncontradoError, CursoService

router = APIRouter(prefix="/cursos", tags=["Cursos"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="US-01: Cadastrar curso (Coordenador)",
)
def criar_curso(
    req: CursoCreateRequest,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> dict[str, str | int]:
    """US-01: Cadastra um novo curso com status RASCUNHO."""
    try:
        modalidade_enum = Modalidade(req.modalidade.lower().strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Modalidade inválida: '{req.modalidade}'. Use 'gravado' ou 'sincrono'.",
        )

    try:
        curso_id, curso = service.cadastrar_curso(
            nome=req.nome,
            descricao=req.descricao,
            modalidade=modalidade_enum,
            carga_horaria=req.carga_horaria,
            data_inicio=req.data_inicio,
            data_fim=req.data_fim,
            inscricao_inicio=req.inscricao_inicio,
            inscricao_fim=req.inscricao_fim,
            vagas=req.vagas,
            valor_matricula=req.valor_matricula,
            cronograma=req.cronograma,
            usuario_autor=coord,
        )
        return {
            "id": curso_id,
            "nome": curso.nome,
            "status": curso.status.value,
            "message": "Curso cadastrado com sucesso em rascunho",
        }
    except (CursoInvalido, PeriodoInvalido) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put(
    "/{curso_id}",
    status_code=status.HTTP_200_OK,
    summary="US-01 c4 · US-03 c3: Editar curso (Coordenador)",
)
def editar_curso(
    curso_id: int,
    req: CursoUpdateRequest,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> dict[str, str]:
    """US-01 c4: Edita dados de um curso revalidando todas as regras."""
    campos = req.model_dump(exclude_unset=True)
    try:
        service.editar_curso(curso_id=curso_id, usuario_autor=coord, **campos)
        return {"message": "Curso atualizado com sucesso"}
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (CursoInvalido, PeriodoInvalido) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/{curso_id}/publicar",
    status_code=status.HTTP_200_OK,
    summary="US-03: Publicar curso (Coordenador)",
)
def publicar_curso(
    curso_id: int,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> dict[str, str]:
    """US-03: Altera o status para PUBLICADO, tornando o curso visível aos alunos."""
    try:
        curso = service.publicar_curso(curso_id=curso_id, usuario_autor=coord)
        return {"id": str(curso_id), "status": curso.status.value, "message": "Curso publicado com sucesso"}
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CursoInvalido as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/{curso_id}/modulos",
    status_code=status.HTTP_201_CREATED,
    summary="US-02: Adicionar módulo (Coordenador)",
)
def adicionar_modulo(
    curso_id: int,
    req: ModuloCreateRequest,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> dict[str, str]:
    """US-02: Cadastra módulo com link URL válido e data do curso se síncrono."""
    try:
        service.adicionar_modulo(
            curso_id=curso_id,
            titulo=req.titulo,
            link=req.link,
            data=req.data,
            usuario_autor=coord,
        )
        return {"message": f"Módulo '{req.titulo}' adicionado com sucesso"}
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ModuloInvalido, CursoInvalido) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{curso_id}/modulos/{posicao}",
    status_code=status.HTTP_200_OK,
    summary="US-02 c2: Remover módulo (Coordenador)",
)
def remover_modulo(
    curso_id: int,
    posicao: int,
    coord: Usuario = Depends(require_coordenador),
    service: CursoService = Depends(get_curso_service),
) -> dict[str, str]:
    """US-02 c2: Remove módulo de um curso pela posição."""
    try:
        mod = service.remover_modulo(curso_id=curso_id, posicao=posicao, usuario_autor=coord)
        return {"message": f"Módulo '{mod.titulo}' removido com sucesso"}
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CursoInvalido as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[CursoResumoResponse],
    summary="US-06: Ver cursos publicados",
)
def listar_cursos_publicados(
    service: CursoService = Depends(get_curso_service),
) -> list[CursoResumoResponse]:
    """US-06 c1, c3, c4: Lista os cursos publicados e sua situação para inscrição."""
    return [CursoResumoResponse(**item) for item in service.listar_cursos_publicados()]


@router.get(
    "/{curso_id}",
    response_model=CursoDetalheResponse,
    summary="US-06 c2: Ver detalhes do curso publicado (sem links)",
)
def obter_detalhes_curso(
    curso_id: int,
    service: CursoService = Depends(get_curso_service),
) -> CursoDetalheResponse:
    """US-06 c2: Mostra os detalhes e títulos dos módulos SEM os links de acesso."""
    try:
        detalhe = service.obter_detalhes_curso(curso_id=curso_id)
        return CursoDetalheResponse(**detalhe)
    except CursoNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CursoInvalido as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

