# Passo 4 — Desenhar a conversa entre os objetos

[← Passo 3](03-responsabilidades.md) · [Projeto da v1](README.md) · próximo: [Passo 5 — Montar as camadas](05-aplicacao-fastapi.md)

Como as classes colaboram para realizar as histórias de usuário que envolvem mais de um objeto e serviços externos (e-mail).

---

## 1. US-07: Aluno se inscreve em curso

Na inscrição, o aluno solicita vaga no curso. O serviço consulta o curso, delega a criação da inscrição respeitando as regras do domínio (vagas, período e duplicidade), persiste o estado e dispara o e-mail com as instruções de pagamento (D-01, RN-01.1).

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant API as API (FastAPI)
    participant Svc as InscricaoService
    participant RepoC as CursoRepository
    participant Curso as Curso
    participant Insc as Inscricao
    participant Email as EmailService

    Aluno ->> API: POST /cursos/{id}/inscrever
    API ->> Svc: inscrever(curso_id, aluno, hoje)
    Svc ->> RepoC: buscar_por_id(curso_id)
    RepoC -->> Svc: curso
    Svc ->> Curso: inscrever(aluno, hoje)
    Note over Curso: Valida: publicado?<br/>dentro do período?<br/>tem vagas?<br/>não duplicado?
    Curso ->> Insc: new(aluno, curso, AGUARDANDO_PAGAMENTO)
    Curso -->> Svc: inscricao
    Svc ->> Email: enviar_instrucoes_pagamento(aluno.email, curso.valor_matricula, chave_pix)
    Email -->> Svc: ok (registrado)
    Svc -->> API: inscricao + instrucoes_pagamento
    API -->> Aluno: 201 Created (detalhes da inscrição + chave Pix)
```

---

## 2. US-08: Coordenador confirma pagamento e libera acesso

O pagamento ocorre fora do sistema (Pix). O coordenador aciona a confirmação na API. O serviço executa a transição de estado da inscrição no domínio, envia o e-mail contendo os links de todos os módulos vigentes (D-03, D-04) e registra a data/hora exata do envio na inscrição (RN-02.5), eliminando o controle manual em planilha/Gmail.

```mermaid
sequenceDiagram
    autonumber
    actor Coord as Coordenador
    participant API as API (FastAPI)
    participant Svc as InscricaoService
    participant RepoC as CursoRepository
    participant Curso as Curso
    participant Insc as Inscricao
    participant Email as EmailService

    Coord ->> API: POST /cursos/{id}/inscricoes/{email}/confirmar
    API ->> Svc: confirmar_pagamento(curso_id, email)
    Svc ->> RepoC: buscar_por_id(curso_id)
    RepoC -->> Svc: curso
    Svc ->> Curso: obter_inscricao(email)
    Curso -->> Svc: inscricao
    Svc ->> Insc: confirmar_pagamento()
    Note over Insc: status = PAGAMENTO_CONFIRMADO<br/>(rejeita se já confirmado)
    Svc ->> Insc: links_liberados()
    Insc ->> Curso: modulos
    Curso -->> Insc: list[Modulo]
    Insc -->> Svc: modulos_com_links
    Svc ->> Email: enviar_links_acesso(aluno.email, curso.nome, modulos)
    Email -->> Svc: enviado em agora
    Svc ->> Insc: registrar_envio_acesso(agora)
    Svc -->> API: inscricao confirmada
    API -->> Coord: 200 OK (status atualizado + data de envio)
```

