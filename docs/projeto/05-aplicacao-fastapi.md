# Passo 5 — Montar as camadas, de baixo para cima

[← Passo 4](04-sequencia.md) · [Projeto da v1](README.md)

Como o sistema é montado do núcleo para fora (arquitetura em camadas / bottom-up), mantendo o domínio em Python puro e usando o FastAPI na interface HTTP.

---

## 1. Ordem de Construção (Bottom-Up)

```
        ▲  [5] API HTTP (FastAPI, Rotas, Schemas Pydantic, Tratamento de Erros)
        │  [4] Serviços de Aplicação (AuthService, CursoService, InscricaoService, EmailService)
        │  [3] Repositórios / Persistência (CursoRepository, UsuarioRepository)
        │  [2] Casos de Uso e Regras de Domínio (Inscricao, Curso, Modulo, Usuario, Periodo)
        │  [1] Tipos Base e Enums (Modalidade, StatusCurso, StatusInscricao, Perfil, Exceções)
```

1. **Domínio (`src/domain/`)**: Python puro, sem dependências de frameworks. Valida regras invariantes, transições de estado e lança exceções especializadas.
2. **Repositórios (`src/repositories/`)**: Abstração de armazenamento em memória com chaves thread-safe para busca e persistência de agregados.
3. **Serviços (`src/services/`)**: Orquestram entidades do domínio, repositórios e serviços de infraestrutura (como envio de e-mails de pagamento e links).
4. **API FastAPI (`src/api/` e `src/main.py`)**: Valida schemas de entrada com Pydantic, gerencia sessões de autenticação, verifica perfis (Aluno vs Coordenador), traduz exceções de domínio em códigos HTTP adequados (400, 404, 409, 422) e formata as respostas.

---

## 2. Mapa História → Endpoint

| US | História | Ator | Método & Rota | Responsabilidade |
|---|---|---|---|---|
| **US-04** | Criar conta de aluno | Visitante | `POST /auth/register` | Cria usuário com perfil `ALUNO`, valida e-mail único e formato |
| **US-05** | Fazer login | Todos | `POST /auth/login` | Valida credenciais (mensagem genérica em caso de erro), gera token/sessão |
| **US-05** | Obter dados da sessão | Autenticado | `GET /auth/me` | Retorna o usuário logado e perfil |
| **US-01** | Cadastrar curso | Coordenador | `POST /cursos` | Cria curso em rascunho com todos os campos obrigatórios |
| **US-01** | Editar curso | Coordenador | `PUT /cursos/{id}` | Edita campos do curso revalidando regras |
| **US-02** | Adicionar módulo | Coordenador | `POST /cursos/{id}/modulos` | Adiciona módulo (Meet ou YouTube, datas dentro do curso se síncrono) |
| **US-02** | Remover módulo | Coordenador | `DELETE /cursos/{id}/modulos/{pos}` | Remove módulo do curso |
| **US-03** | Publicar curso | Coordenador | `POST /cursos/{id}/publicar` | Altera status para `PUBLICADO` |
| **US-06** | Listar cursos publicados | Público / Aluno | `GET /cursos` | Lista cursos visíveis com indicação de situação ("inscrições abertas", etc.) |
| **US-06** | Ver detalhes de curso | Público / Aluno | `GET /cursos/{id}` | Mostra detalhes e módulos **sem os links** de acesso |
| **US-07** | Inscrever-se em curso | Aluno | `POST /cursos/{id}/inscrever` | Cria inscrição em rascunho e envia instruções Pix por e-mail |
| **US-08** | Listar inscritos | Coordenador | `GET /cursos/{id}/inscritos` | Lista nome, email, data e status de cada inscrito |
| **US-08** | Confirmar pagamento | Coordenador | `POST /cursos/{id}/inscricoes/{email}/confirmar` | Confirma pagamento, dispara e-mail com links e grava carimbo de data/hora |
| **US-09** | Meus cursos | Aluno | `GET /meus-cursos` | Lista inscrições do aluno com status |
| **US-09** | Detalhes e links do meu curso | Aluno | `GET /meus-cursos/{id}` | Se pago: exibe os links atualizados; se pendente: exibe instruções sem links |

