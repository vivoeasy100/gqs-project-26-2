"""Exceções de domínio (Passo 3 - regras recusam com erro do domínio)."""


class DominioError(Exception):
    """Erro base do domínio."""
    pass


class PeriodoInvalido(DominioError):
    """Data final anterior à inicial."""
    pass


class CursoInvalido(DominioError):
    """Erro de validação do curso."""
    pass


class InscricaoDuplicada(DominioError):
    """Aluno já inscrito no curso."""
    pass


class VagasEsgotadas(DominioError):
    """Sem vagas disponíveis."""
    pass


class ForaDoPeriodoInscricao(DominioError):
    """Fora do período de inscrição."""
    pass


class CursoNaoPublicado(DominioError):
    """Curso não está publicado."""
    pass


class ModuloInvalido(DominioError):
    """Erro de validação do módulo."""
    pass


class UsuarioInvalido(DominioError):
    """Erro de validação do usuário."""
    pass


class InscricaoInvalida(DominioError):
    """Erro de validação da inscrição."""
    pass


class PagamentoJaConfirmado(DominioError):
    """Pagamento já foi confirmado."""
    pass