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

## Health Check

Endpoint utilizado para verificar a disponibilidade da aplicação.

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| GET | `/identidade-token/api/v1/health/` | Verifica se o serviço está disponível. |

---

### Perfil

Conjunto de endpoints responsáveis pelo gerenciamento da projeção de autorização dos usuários.

### Consultar projeção de usuário

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| GET | `/identidade-token/api/v1/perfis/{usuario_id}` | Consulta a projeção de autorização de um usuário. |

### Sincronizar projeção de usuário

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| PUT | `/identidade-token/api/v1/perfis/{usuario_id}` | Cria ou atualiza a projeção de autorização de um usuário. |

### Consultar sistemas do usuário

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| GET | `/identidade-token/api/v1/perfis/{usuario_id}/sistemas/` | Retorna a lista de sistemas distintos aos quais o usuário tem acesso, derivada de suas permissões de módulo. |

> **Observação**
>
> Se a projeção do usuário existir mas não houver nenhuma permissão de módulo associada, a resposta é **200** com `sistemas: []` — lista vazia é uma resposta válida, não um erro. Retorna **404** apenas quando o `usuario_id` informado não corresponder a nenhuma projeção de usuário.

---

## Tokens

Conjunto de endpoints responsáveis pela emissão, validação e publicação das chaves utilizadas pelos Tokens JWT Enriquecidos.

### Gerar Token JWT Enriquecido

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| POST | `/identidade-token/api/v1/token/enriquecido/{usuario_id}` | Compõe e emite um novo Token JWT Enriquecido para o usuário informado. |

### Validar Token JWT

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| POST | `/identidade-token/api/v1/token/validar/` | Valida a assinatura, integridade e expiração de um Token JWT Enriquecido. |

### Publicar JWKS

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| GET | `/identidade-token/.well-known/jwks.json` | Publica o conjunto de chaves públicas (JWKS) utilizadas para validação dos Tokens JWT Enriquecidos. |

> **Observação**
>
> O endpoint JWKS é público e segue o padrão **JSON Web Key Set (JWKS)** definido pela RFC 7517, permitindo que sistemas consumidores validem a assinatura dos tokens emitidos pelo Token-MS.

---

# OpenAPI

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
