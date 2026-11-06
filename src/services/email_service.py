"""Serviço de envio e registro de e-mails do sistema."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from threading import Lock
from domain.modulo import Modulo


@dataclass(frozen=True)
class EmailEnviado:
    """Registro de um e-mail emitido pelo sistema."""

    destinatario: str
    assunto: str
    conteudo: str
    tipo: str  # "instrucoes_pagamento" ou "links_acesso"
    enviado_em: datetime


class EmailService:
    """Simulador e gerenciador de e-mails em memória com auditoria."""

    def __init__(self, chave_pix_padrao: str = "pix@cursoseduca.com.br") -> None:
        self.chave_pix_padrao = chave_pix_padrao
        self._enviados: list[EmailEnviado] = []
        self._lock = Lock()

    def enviar_instrucoes_pagamento(
        self,
        destinatario: str,
        curso_nome: str,
        valor: Decimal,
        chave_pix: str | None = None,
        agora: datetime | None = None,
    ) -> EmailEnviado:
        """US-07 c2: Envia e-mail com o valor da matrícula e chave Pix para pagamento."""
        chave = chave_pix or self.chave_pix_padrao
        timestamp = agora or datetime.now()
        assunto = f"Instruções de Pagamento - Curso {curso_nome}"
        conteudo = (
            f"Olá! Sua inscrição no curso '{curso_nome}' foi registrada com sucesso.\n"
            f"Valor da matrícula: R$ {valor:.2f}\n"
            f"Chave Pix para pagamento: {chave}\n"
            f"Após o pagamento, a coordenação confirmará seu acesso."
        )
        email = EmailEnviado(
            destinatario=destinatario,
            assunto=assunto,
            conteudo=conteudo,
            tipo="instrucoes_pagamento",
            enviado_em=timestamp,
        )
        with self._lock:
            self._enviados.append(email)
        return email

    def enviar_links_acesso(
        self,
        destinatario: str,
        curso_nome: str,
        modulos: list[Modulo],
        agora: datetime | None = None,
    ) -> EmailEnviado:
        """US-08 c2, c4: Envia e-mail com os links de acesso dos módulos após confirmação."""
        timestamp = agora or datetime.now()
        linhas_modulos = []
        for mod in modulos:
            data_str = f" ({mod.data.strftime('%d/%m/%Y')})" if mod.data else ""
            linhas_modulos.append(f"- {mod.titulo}{data_str}: {mod.link}")

        modulos_texto = "\n".join(linhas_modulos) if linhas_modulos else "Módulos serão disponibilizados em breve."
        assunto = f"Acesso Liberado - Curso {curso_nome}"
        conteudo = (
            f"Parabéns! Seu pagamento para o curso '{curso_nome}' foi confirmado.\n\n"
            f"Aqui estão seus links de acesso:\n{modulos_texto}\n\n"
            f"Bons estudos!"
        )
        email = EmailEnviado(
            destinatario=destinatario,
            assunto=assunto,
            conteudo=conteudo,
            tipo="links_acesso",
            enviado_em=timestamp,
        )
        with self._lock:
            self._enviados.append(email)
        return email

    def obter_emails_por_destinatario(self, destinatario: str) -> list[EmailEnviado]:
        """Consulta todos os e-mails enviados para um determinado aluno."""
        alvo = destinatario.lower().strip()
        with self._lock:
            return [e for e in self._enviados if e.destinatario.lower().strip() == alvo]

    def listar_todos(self) -> list[EmailEnviado]:
        """Retorna histórico completo de e-mails emitidos."""
        with self._lock:
            return list(self._enviados)

    def limpar(self) -> None:
        """Limpa registros de e-mails."""
        with self._lock:
            self._enviados.clear()

