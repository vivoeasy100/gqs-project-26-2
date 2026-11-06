"""Serviço de Aplicação para Cursos e Inscrições (US-01 a US-03, US-06 a US-09)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from domain.curso import Curso
from domain.enums import Modalidade, StatusCurso, StatusInscricao
from domain.exceptions import CursoInvalido, DominioError, InscricaoInvalida
from domain.inscricao import Inscricao
from domain.modulo import Modulo
from domain.periodo import Periodo
from domain.usuario import Usuario
from repositories.curso_repository import CursoRepository
from services.email_service import EmailEnviado, EmailService


class AcessoNegadoError(Exception):
    """Usuário não possui permissão para executar a ação."""
    pass


class CursoNaoEncontradoError(Exception):
    """Curso pesquisado não existe."""
    pass


class InscricaoNaoEncontradaError(Exception):
    """Inscrição não localizada."""
    pass


class CursoService:
    """Orquestrador das regras de negócio e histórias de uso de Cursos e Inscrições."""

    def __init__(
        self,
        curso_repo: CursoRepository,
        email_service: EmailService,
    ) -> None:
        self.curso_repo = curso_repo
        self.email_service = email_service

    def _exigir_coordenador(self, usuario: Usuario) -> None:
        """Garante que a operação é realizada por um coordenador."""
        if not usuario.eh_coordenador():
            raise AcessoNegadoError("Ação permitida apenas para a coordenação de cursos")

    def _obter_curso(self, curso_id: int) -> Curso:
        """Busca curso ou lança erro 404 de domínio."""
        curso = self.curso_repo.buscar_por_id(curso_id)
        if not curso:
            raise CursoNaoEncontradoError(f"Curso {curso_id} não encontrado")
        return curso

    # --- US-01: Cadastrar e Editar Curso ---

    def cadastrar_curso(
        self,
        *,
        nome: str,
        descricao: str,
        modalidade: Modalidade,
        carga_horaria: int,
        data_inicio: date,
        data_fim: date,
        inscricao_inicio: date,
        inscricao_fim: date,
        vagas: int,
        valor_matricula: Decimal,
        cronograma: str = "",
        usuario_autor: Usuario,
    ) -> tuple[int, Curso]:
        """US-01: Cadastra um novo curso com status RASCUNHO."""
        self._exigir_coordenador(usuario_autor)

        datas_curso = Periodo(inicio=data_inicio, fim=data_fim)
        periodo_inscricao = Periodo(inicio=inscricao_inicio, fim=inscricao_fim)

        curso = Curso(
            nome=nome,
            descricao=descricao,
            modalidade=modalidade,
            carga_horaria=carga_horaria,
            datas=datas_curso,
            periodo_inscricao=periodo_inscricao,
            vagas=vagas,
            valor_matricula=valor_matricula,
            cronograma=cronograma,
            status=StatusCurso.RASCUNHO,
        )

        curso_id = self.curso_repo.salvar(curso)
        return curso_id, curso

    def editar_curso(
        self,
        curso_id: int,
        usuario_autor: Usuario,
        **campos: Any,
    ) -> Curso:
        """US-01 c4 · US-03 c3: Editar dados do curso revalidando todas as regras."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)

        # Tratar períodos se passados como datas separadas
        if "data_inicio" in campos or "data_fim" in campos:
            novo_inicio = campos.pop("data_inicio", curso.datas.inicio)
            novo_fim = campos.pop("data_fim", curso.datas.fim)
            campos["datas"] = Periodo(inicio=novo_inicio, fim=novo_fim)

        if "inscricao_inicio" in campos or "inscricao_fim" in campos:
            novo_inicio = campos.pop("inscricao_inicio", curso.periodo_inscricao.inicio)
            novo_fim = campos.pop("inscricao_fim", curso.periodo_inscricao.fim)
            campos["periodo_inscricao"] = Periodo(inicio=novo_inicio, fim=novo_fim)

        curso.editar(**campos)
        self.curso_repo.atualizar(curso_id, curso)
        return curso

    # --- US-02: Gerenciar Módulos ---

    def adicionar_modulo(
        self,
        curso_id: int,
        *,
        titulo: str,
        link: str,
        data: date | None = None,
        usuario_autor: Usuario,
    ) -> Modulo:
        """US-02: Adiciona módulo ao curso com validação de URL e datas."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)

        modulo = Modulo(titulo=titulo, link=link, data=data)
        curso.adicionar_modulo(modulo)
        return modulo

    def remover_modulo(
        self,
        curso_id: int,
        posicao: int,
        usuario_autor: Usuario,
    ) -> Modulo:
        """US-02 c2: Remove módulo pela posição (índice 0-based)."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)

        if posicao < 0 or posicao >= len(curso.modulos):
            raise CursoInvalido(f"Módulo na posição {posicao} não existe")

        modulo = curso.modulos[posicao]
        curso.remover_modulo(modulo)
        return modulo

    # --- US-03: Publicar Curso ---

    def publicar_curso(self, curso_id: int, usuario_autor: Usuario) -> Curso:
        """US-03 c1: Publica o curso tornando-o visível."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)
        curso.publicar()
        return curso

    # --- US-06: Ver Cursos Publicados ---

    def listar_cursos_publicados(
        self, hoje: date | None = None
    ) -> list[dict[str, Any]]:
        """US-06 c1, c3, c4: Lista apenas cursos publicados com sua situação."""
        dia = hoje or date.today()
        todos = self.curso_repo.listar()
        resultado = []

        for cid, c in todos:
            if not c.visivel_para_aluno():
                continue
            resultado.append({
                "id": cid,
                "nome": c.nome,
                "modalidade": c.modalidade.value,
                "carga_horaria": c.carga_horaria,
                "data_inicio": c.datas.inicio,
                "data_fim": c.datas.fim,
                "periodo_inscricao_inicio": c.periodo_inscricao.inicio,
                "periodo_inscricao_fim": c.periodo_inscricao.fim,
                "vagas": c.vagas,
                "vagas_ocupadas": c.vagas_ocupadas(),
                "valor_matricula": c.valor_matricula,
                "situacao": c.situacao(dia),
                "aceita_inscricoes": c.aceita_inscricoes(dia),
            })
        return resultado

    def obter_detalhes_curso(
        self, curso_id: int, hoje: date | None = None
    ) -> dict[str, Any]:
        """US-06 c2: Detalhes do curso e títulos dos módulos SEM os links."""
        dia = hoje or date.today()
        curso = self._obter_curso(curso_id)
        if not curso.visivel_para_aluno():
            raise CursoInvalido("Curso não está visível para alunos")

        modulos_publicos = [
            {"titulo": m.titulo, "data": m.data}
            for m in curso.modulos
        ]

        return {
            "id": curso_id,
            "nome": curso.nome,
            "descricao": curso.descricao,
            "cronograma": curso.cronograma,
            "modalidade": curso.modalidade.value,
            "carga_horaria": curso.carga_horaria,
            "data_inicio": curso.datas.inicio,
            "data_fim": curso.datas.fim,
            "periodo_inscricao_inicio": curso.periodo_inscricao.inicio,
            "periodo_inscricao_fim": curso.periodo_inscricao.fim,
            "vagas": curso.vagas,
            "vagas_ocupadas": curso.vagas_ocupadas(),
            "valor_matricula": curso.valor_matricula,
            "situacao": curso.situacao(dia),
            "aceita_inscricoes": curso.aceita_inscricoes(dia),
            "modulos": modulos_publicos,
        }

    # --- US-07: Inscrever-se em Curso ---

    def inscrever_aluno(
        self,
        curso_id: int,
        aluno: Usuario,
        hoje: date | None = None,
        agora: datetime | None = None,
    ) -> dict[str, Any]:
        """US-07: Realiza inscrição, gera instruções e envia e-mail."""
        if aluno.eh_coordenador():
            raise InscricaoInvalida("Coordenadores não podem se inscrever como alunos")

        dia = hoje or date.today()
        curso = self._obter_curso(curso_id)

        # Delega ao domínio que verifica período, vagas e duplicidade
        inscricao = curso.inscrever(aluno, dia)

        # Dispara e-mail com instruções de pagamento Pix (US-07 c2)
        email_msg = self.email_service.enviar_instrucoes_pagamento(
            destinatario=aluno.email,
            curso_nome=curso.nome,
            valor=curso.valor_matricula,
            agora=agora,
        )

        return {
            "curso_id": curso_id,
            "curso_nome": curso.nome,
            "aluno_nome": aluno.nome,
            "aluno_email": aluno.email,
            "status": inscricao.status.value,
            "valor_matricula": curso.valor_matricula,
            "chave_pix": self.email_service.chave_pix_padrao,
            "instrucoes_pagamento": email_msg.conteudo,
        }

    # --- US-08: Ver Inscritos e Confirmar Pagamento ---

    def listar_inscritos(
        self, curso_id: int, usuario_autor: Usuario
    ) -> list[dict[str, Any]]:
        """US-08 c1: Lista inscritos com nome, e-mail, data e status."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)

        return [
            {
                "nome": insc.aluno.nome,
                "email": insc.aluno.email,
                "data": insc.data,
                "status": insc.status.value,
                "acesso_enviado_em": insc.acesso_enviado_em,
            }
            for insc in curso.inscricoes
        ]

    def confirmar_pagamento(
        self,
        curso_id: int,
        aluno_email: str,
        usuario_autor: Usuario,
        agora: datetime | None = None,
    ) -> dict[str, Any]:
        """US-08 c2, c3, c4: Confirma pagamento, libera acesso, envia e-mail com links e carimba data."""
        self._exigir_coordenador(usuario_autor)
        curso = self._obter_curso(curso_id)
        momento = agora or datetime.now()

        inscricao: Inscricao | None = None
        for insc in curso.inscricoes:
            if insc.aluno.email.lower().strip() == aluno_email.lower().strip():
                inscricao = insc
                break

        if not inscricao:
            raise InscricaoNaoEncontradaError(f"Inscrição do aluno {aluno_email} não encontrada neste curso")

        # Regra de domínio: muda status e recusa se já confirmado (US-08 c2, c3)
        inscricao.confirmar_pagamento()

        # Obtém links liberados atualizados (US-09 c4) e envia e-mail
        modulos = inscricao.links_liberados()
        email_enviado = self.email_service.enviar_links_acesso(
            destinatario=inscricao.aluno.email,
            curso_nome=curso.nome,
            modulos=modulos,
            agora=momento,
        )

        # Registra carimbo de auditoria de envio de acesso (US-08 c4)
        inscricao.registrar_envio_acesso(momento)

        return {
            "curso_id": curso_id,
            "aluno_email": inscricao.aluno.email,
            "status": inscricao.status.value,
            "acesso_enviado_em": inscricao.acesso_enviado_em,
            "modulos_liberados_total": len(modulos),
        }

    # --- US-09: Ver Meus Cursos e Links de Acesso ---

    def listar_meus_cursos(self, aluno: Usuario) -> list[dict[str, Any]]:
        """US-09 c1: Lista cursos em que o aluno está inscrito e status."""
        inscricoes_aluno = self.curso_repo.buscar_inscricoes_por_aluno(aluno.email)
        resultado = []
        for cid, curso, insc in inscricoes_aluno:
            resultado.append({
                "curso_id": cid,
                "curso_nome": curso.nome,
                "modalidade": curso.modalidade.value,
                "status_inscricao": insc.status.value,
                "acesso_liberado": insc.acesso_liberado(),
                "data_inscricao": insc.data,
            })
        return resultado

    def obter_meu_curso_detalhe(
        self, curso_id: int, aluno: Usuario
    ) -> dict[str, Any]:
        """US-09 c2, c3, c4: Se confirmado, mostra links; se aguardando, mostra instruções de pagamento."""
        curso = self._obter_curso(curso_id)

        inscricao: Inscricao | None = None
        for insc in curso.inscricoes:
            if insc.aluno.email.lower().strip() == aluno.email.lower().strip():
                inscricao = insc
                break

        if not inscricao:
            raise InscricaoNaoEncontradaError(f"Você não está inscrito no curso {curso_id}")

        dados: dict[str, Any] = {
            "curso_id": curso_id,
            "curso_nome": curso.nome,
            "descricao": curso.descricao,
            "modalidade": curso.modalidade.value,
            "status_inscricao": inscricao.status.value,
            "acesso_liberado": inscricao.acesso_liberado(),
        }

        if inscricao.acesso_liberado():
            # US-09 c2, c4: Links sempre atualizados diretamente do curso
            dados["modulos"] = [
                {
                    "titulo": m.titulo,
                    "link": m.link,
                    "data": m.data,
                }
                for m in inscricao.links_liberados()
            ]
        else:
            # US-09 c3: Sem links, instruções de pagamento
            dados["modulos"] = [
                {"titulo": m.titulo, "data": m.data}
                for m in curso.modulos
            ]
            dados["instrucoes_pagamento"] = (
                f"Sua inscrição está aguardando pagamento no valor de R$ {curso.valor_matricula:.2f}. "
                f"Utilize a chave Pix: {self.email_service.chave_pix_padrao}. "
                "Assim que a coordenação confirmar o pagamento, os links de acesso serão liberados aqui e por e-mail."
            )

        return dados

