# API

Esta seção apresenta uma visão geral dos recursos disponibilizados pelo **SME-Identidade-Token-Microsservico**.

## Autenticação

Todos os endpoints protegidos utilizam autenticação por **API Key**.

A chave deve ser enviada no cabeçalho HTTP configurado pela variável de ambiente `API_KEY_HEADER`.

Exemplo:
```text
X-API-Key: <API_KEY>
```

Caso a chave seja inválida ou esteja ausente, a requisição será rejeitada com **HTTP 401 (Unauthorized)**.

## Recursos disponíveis

### Health Check

Endpoint utilizado para verificar a disponibilidade da aplicação.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/identidade-token/api/v1/health/` | Verifica se o serviço está disponível. |

---

### Perfil

Conjunto de endpoints responsáveis pelo gerenciamento da projeção de autorização dos usuários.

#### Consultar projeção de usuário

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/identidade-token/api/v1/perfis/{usuario_id}` | Consulta a projeção de um usuário. |

#### Sincronizar projeção de usuário

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| PUT | `/identidade-token/api/v1/perfis/{usuario_id}` | Cria ou atualiza a projeção de autorização de um usuário. |

## OpenAPI

A documentação completa da API pode ser consultada através do Swagger da aplicação.

Ela inclui:

- contratos de requisição e resposta;
- parâmetros;
- payloads;
- schemas;
- códigos de resposta;
- exemplos de utilização.

A documentação completa da API está disponível em:

- `/identidade-token/api/v1/docs/`