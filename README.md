# Sistema de Gestão de Cursos Online — v1

> **Aluno:** Fernando Almeida  
> **RA:** 326132695  
> **Disciplina:** Gestão e Qualidade de Software (GQS)  
> **Data de Entrega:** 05/11/2026  

---

## 📌 Sobre o Projeto

Este projeto consiste na implementação da **versão 1 (v1)** do sistema próprio para gestão, publicação, inscrição e liberação de acesso a cursos online. A solução substitui os processos manuais legados (uso de Sympla para inscrições e envio manual de e-mails em cópia oculta pelo Gmail), automatizando o fluxo de auditoria de pagamentos e a entrega dos links de acesso.

O desenvolvimento foi conduzido seguindo a metodologia **Bottom-Up** (Vasconcelos et al., 2006; Sommerville, 2016), estruturando primeiramente o domínio em Python puro desacoplado de frameworks e, em seguida, construindo as camadas de persistência, serviços de aplicação e interface HTTP com FastAPI.

---

## 🛠️ Tecnologias e Aplicações Utilizadas

| Tecnologia / Ferramenta | Finalidade |
|---|---|
| **Python 3.12** | Linguagem principal do ecossistema |
| **FastAPI (0.162+)** | Framework web moderno para construção da API RESTful |
| **Pydantic v2** | Validação estrita de contratos de dados (schemas) e serialização |
| **Uvicorn** | Servidor ASGI para execução assíncrona da aplicação |
| **Pytest (9.2+)** | Framework de testes automatizados de unidade e integração |
| **Pytest-Cov (5.0+)** | Medição e relatório de cobertura de código (HTML e terminal) |
| **Hashlib & Secrets (PBKDF2-SHA256)** | Criptografia de senhas e geração de tokens de sessão seguros |
| **Mermaid & BPMN 2.0** | Modelagem de processos AS-IS, diagramas de classe, estado e sequência |

---

## 🏗️ Arquitetura do Sistema (Camadas Bottom-Up)

```
        ▲  [4] API HTTP (FastAPI, Rotas, Schemas Pydantic, Middlewares)
        │  [3] Serviços de Aplicação (AuthService, CursoService, EmailService)
        │  [2] Repositórios / Persistência (CursoRepository, UsuarioRepository)
        │  [1] Domínio Puro (Curso, Modulo, Inscricao, Usuario, Periodo, Enums, Regras)
```

1. **`src/domain/` (Domínio Puro):**
   - Entidades e Value Objects: `Curso`, `Modulo`, `Inscricao`, `Usuario`, `Periodo`.
   - Enums: `Modalidade` (gravado/síncrono), `StatusCurso` (rascunho/publicado), `StatusInscricao` (aguardando/confirmado), `Perfil` (aluno/coordenador).
   - Exceções customizadas que recusam operações inválidas com erros de domínio.
2. **`src/repositories/` (Persistência em Memória):**
   - `UsuarioRepository`: busca por e-mail, unicidade e persistência de credenciais.
   - `CursoRepository`: armazenamento com chave incremental e busca de matrículas por aluno.
3. **`src/services/` (Serviços de Aplicação):**
   - `AuthService`: cadastro de alunos, login com mensagem genérica em falhas e tokens de sessão.
   - `EmailService`: envio simulado com auditoria de instruções Pix e e-mails com links de acesso.
   - `CursoService`: orquestração das regras de negócio das histórias US-01 a US-09.
4. **`src/api/` e `src/main.py` (FastAPI):**
   - Rotas organizadas por contexto (`routes_auth`, `routes_cursos`, `routes_inscricoes`).
   - Segurança baseada em dependências (`require_coordenador`, `require_aluno`).
   - Tratamento global de exceções de domínio mapeadas para códigos HTTP (400, 401, 403, 404, 409).

---

## 📋 Histórias de Usuário Implementadas (v1)

| US | Título | Persona | Rota / Método | Status |
|---|---|---|---|---|
| **US-01** | Cadastrar e Editar Curso | Coordenador | `POST /cursos`, `PUT /cursos/{id}` | ✅ Implementado |
| **US-02** | Gerenciar Módulos do Curso | Coordenador | `POST /cursos/{id}/modulos`, `DELETE ...` | ✅ Implementado |
| **US-03** | Publicar Curso | Coordenador | `POST /cursos/{id}/publicar` | ✅ Implementado |
| **US-04** | Criar Conta de Aluno | Aluno | `POST /auth/register` | ✅ Implementado |
| **US-05** | Fazer Login e Logout | Aluno / Coordenador | `POST /auth/login`, `POST /auth/logout` | ✅ Implementado |
| **US-06** | Ver Cursos Publicados (sem links) | Aluno / Público | `GET /cursos`, `GET /cursos/{id}` | ✅ Implementado |
| **US-07** | Inscrever-se em Curso | Aluno | `POST /cursos/{id}/inscrever` | ✅ Implementado |
| **US-08** | Ver Inscritos e Confirmar Pagamento | Coordenador | `GET /cursos/{id}/inscritos`, `POST .../confirmar` | ✅ Implementado |
| **US-09** | Ver Meus Cursos e Links Liberados | Aluno | `GET /meus-cursos`, `GET /meus-cursos/{id}` | ✅ Implementado |

---

## ✅ Testes Automatizados e Cobertura

A suíte conta com **86 testes automatizados**, cobrindo regras do domínio, casos de uso dos serviços e integração completa de ponta a ponta das rotas HTTP da API.

### Resultado da Execução do Pytest

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: E:\Projetos GitHub\gqs-project-26-2\gqs-project-26-2
configfile: pytest.ini
collected 86 items

tests/test_curso.py .........................................          [ 48%]
tests/test_inscricao.py .............                                  [ 63%]
tests/test_modulo.py ........                                          [ 72%]
tests/test_periodo.py .....                                            [ 78%]
tests/test_usuario.py .......                                          [ 86%]
tests/test_services.py .......                                         [ 94%]
tests/test_api.py .....                                                [100%]

---------- coverage: platform win32, python 3.12.10 ----------
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
src\domain\__init__.py         0      0   100%
src\domain\curso.py          120      2    98%   39, 123
src\domain\enums.py           13      0   100%
src\domain\exceptions.py      22      0   100%
src\domain\inscricao.py       36      1    97%   22
src\domain\modulo.py          15      0   100%
src\domain\periodo.py         14      0   100%
src\domain\usuario.py         17      0   100%
--------------------------------------------------------
TOTAL                        237      3    99%

Required test coverage of 80% reached. Total coverage: 98.73%
============================= 86 passed in 8.33s ==============================
```

- **Total de testes:** 86
- **Testes aprovados:** 86 (100% de sucesso)
- **Cobertura de código do domínio:** 98.73% (meta mínima exigida: 80%)

---

## 🚀 Como Executar o Projeto

### 1. Clonar o repositório e entrar no diretório
```bash
git clone https://github.com/fernandoalmeida/gqs-project-26-2.git
cd gqs-project-26-2/gqs-project-26-2
```

### 2. Instalar as dependências
```bash
pip install -r pyproject.toml
# ou
pip install fastapi uvicorn pydantic pytest pytest-cov pytest-mock
```

### 3. Rodar os testes automatizados
```bash
pytest
```
*Gera também o relatório visual de cobertura na pasta `htmlcov/index.html`.*

### 4. Iniciar a API com FastAPI e Uvicorn
```bash
python -m uvicorn main:app --reload --app-dir src
```

Acesse a documentação interativa Swagger UI em:
👉 **http://localhost:8000/docs**

