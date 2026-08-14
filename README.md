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
│   └── tokens/         # Emissão, validação e publicação dos Tokens JWT
│   └── cache/          # camada de cache utilizando KeyDB
├── config/             # settings, urls, wsgi
├── docs/               # Documentação Sphinx
├── requirements/
│   ├── base.txt        # dependências de produção
│   └── local.txt       # base + ferramentas de desenvolvimento
├── scripts/            # Scripts auxiliares
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

---

## apps/tokens

Domínio responsável pela emissão e validação dos Tokens JWT Enriquecidos.

| Módulo | Responsabilidade |
|---------|------------------|
| `api/views.py` | Endpoints para emissão, validação e publicação do JWKS. |
| `api/serializers.py` | Contratos de entrada e saída dos endpoints de Token. |
| `api/urls.py` | Registro das rotas do domínio Tokens. |
| `services.py` | Orquestração da geração do Token JWT Enriquecido, incluindo integração com a camada de cache. |
| `token_enriquecido.py` | Composição e assinatura do Token JWT Enriquecido. |
| `libs/jwt_chaves.py` | Gerenciamento das chaves criptográficas utilizadas pelo serviço. |
| `libs/jwks.py` | Construção do documento JWKS publicado pelo serviço. |
| `libs/jwt_validacao.py` | Validação da assinatura e das claims dos Tokens JWT. |

---

## apps/cache

Domínio responsável pelo gerenciamento da camada de cache utilizando KeyDB.

| Módulo | Responsabilidade |
|---------|------------------|
| `services.py` | Serviço responsável pelo armazenamento, recuperação e invalidação dos dados em cache. |
| `chaves.py` | Centralização da geração das chaves utilizadas para identificação dos registros armazenados. |

---

## Requisitos

- Python 3.12+
- Docker e Docker Compose
- OpenSSL (apenas para geração das chaves em ambiente de desenvolvimento)

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
| `JWT_ENRIQUECIDO_PRIVATE_KEY_PATH` | Caminho da chave privada utilizada para assinatura dos tokens. |
| `JWT_ENRIQUECIDO_PUBLIC_KEY_PATH` | Caminho da chave pública publicada no JWKS. |
| `JWT_ENRIQUECIDO_KID` | Identificador da chave utilizada no Header do JWT. |
| `JWT_ENRIQUECIDO_ALGORITMO` | Algoritmo utilizado na assinatura dos tokens. |
| `JWT_ENRIQUECIDO_TTL_SEGUNDOS` | Tempo de vida (TTL), em segundos, dos Tokens JWT Enriquecidos emitidos pelo serviço. |
| `URL_KEYDB` | `redis://keydb:6379/0` | URL de conexão com o serviço KeyDB utilizado pela camada de cache para armazenamento e recuperação dos Tokens JWT Enriquecidos. |
| `KEYDB_DEFAULT_TIMEOUT` | `300` | Tempo de vida (TTL), em segundos, das entradas armazenadas no cache KeyDB. Após esse período, os registros expiram automaticamente. |

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