# SME-Identidade-Token-Microsservico

O SME-Identidade-Token-Microsservico é responsável pela composição e enriquecimento de atributos de autorização utilizados pelos sistemas da SME-SP.

Atuando como camada complementar ao Keycloak, o serviço desacopla regras de autorização, atributos corporativos e projeções legadas do provedor de identidade, disponibilizando tokens enriquecidos com o contexto de acesso necessário para os consumidores da plataforma.

## Estrutura do repositório

```
.
├── apps/
│   ├── core/           # cliente HTTP
│   └── autenticacao/   # domínio autenticação: views, services, serializers
│   └── perfil/         # domínio perfil: views, services, serializers, models
├── config/             # settings, urls, wsgi
├── requirements/
│   ├── base.txt        # dependências de produção
│   └── local.txt       # base + ferramentas de desenvolvimento
└── manage.py
```

### apps/core

| Módulo | Responsabilidade |
|---|---|
| `api/views.py` | Endpoints da aplicação, incluindo o health check do serviço |
| `api/serializers.py` | Serialização e validação de dados de entrada e saída |
| `api/urls.py` | Registro e roteamento das URLs da aplicação |

### apps/autenticacao

| Módulo | Responsabilidade |
|---|---|
| `api/autenticacao.py` | Implementa a autenticação dos endpoints por **API Key**, validando a chave enviada no cabeçalho HTTP configurado pela aplicação. |

### apps/perfil

| Módulo | Responsabilidade |
|---|---|
| `api/views.py`       | Endpoints para consulta e sincronização da projeção de usuários, incluindo seus perfis e permissões. |
| `api/serializers.py` | Serialização, validação e persistência dos dados da projeção de usuários. |
| `api/urls.py`        | Registro e roteamento das rotas do domínio de perfil. |
| `models.py`          | Modelos responsáveis pelo armazenamento da projeção de usuários, perfis e permissões. |

## Requisitos

- Python 3.12+
- Docker e Docker Compose

## Instalação para desenvolvimento

Crie um ambiente virtual e instale as dependências locais:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements/local.txt
```

Instale os hooks do `pre-commit` antes de criar o primeiro commit:

```bash
pre-commit install
pre-commit run --all-files
```

O `pre-commit install` é obrigatório no setup local. Depois de instalado, os
formatadores e validadores são executados automaticamente em cada commit,
evitando o envio de código fora do padrão do projeto.

## Configuração do ambiente

```bash
cp .env.example .env
make build
make run
```

**Geral**

| Variável | Padrão | Descrição |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Chave secreta do Django |
| `DJANGO_DEBUG` | `1` | Ativa o modo debug (`0` em produção) |
| `DJANGO_ALLOWED_HOSTS` | `*` | Hosts permitidos, separados por vírgula |
| `API_KEY` | - | Chave de autenticação utilizada para validar o acesso às APIs protegidas pela aplicação. |
| `API_KEY_HEADER` | `X-API-Key` | Nome do cabeçalho HTTP utilizado para enviar a chave de autenticação nas requisições. |
| `IDENTIDADE_TOKEN_DB_URL` | - | URL de conexão com o banco de dados. |

## Atalhos Make

Use `make help` para listar todos os comandos disponíveis. Os principais:

**Ambiente**

| Comando | Descrição |
|---|---|
| `make run` | Sobe o containers em modo dev (porta 8002) |
| `make build` | Rebuild da imagem dev |
| `make stop` | Para e remove containers |

**Migrações**

| Comando | Descrição |
|---|---|
| `make migrate` | Aplica migrations no `IDENTIDADE_TOKEN_DB` |

**Testes**

| Comando | Descrição |
|---|---|
| `make test` | Suite completa com cobertura ≥ 80% |
| `make test-core` | Apenas `apps.core` |

**Qualidade**

| Comando | Descrição |
|---|---|
| `make lint` | ruff + black + isort + mypy |
| `make coverage` | Relatório HTML em `docs/_cov/` |
| `make schema` | Gera schema OpenAPI em `schema.yml` |
| `make docs` | Gera documentação Sphinx em `docs/_build/html/` |

## Endpoints

Consulte o Swagger em `identidade-token/api/v1/docs/` para a lista completa de rotas com parâmetros e exemplos de resposta.