# Fluxo do Token JWT Enriquecido

## Objetivo

O Token JWT Enriquecido é um JWT próprio da plataforma, emitido pelo **SME-Identidade-Token-Microsservico**.

Seu objetivo é disponibilizar aos sistemas consumidores uma representação consolidada das informações de autorização do usuário, reunindo atributos provenientes do Keycloak e das projeções mantidas pelo Token-MS.

Esse token **não substitui** o Access Token emitido pelo Keycloak. O Keycloak continua sendo responsável pela autenticação dos usuários, enquanto o Token-MS é responsável pela composição e emissão do Token JWT Enriquecido.

---

## Fluxo de emissão

```text
                 Cliente

                    │

                    ▼

              Auth Gateway

                    │

                    ▼

        Keycloak autentica usuário

                    │

                    ▼

              Auth Gateway

                    │

                    ▼

             Token-MS recebe

                    │

                    ▼

        Consulta projeções do usuário

                    │

                    ▼

        Compõe o Token JWT Enriquecido

                    │

                    ▼

          Assina utilizando RS256

                    │

                    ▼

        Retorna o JWT ao Gateway

                    │

                    ▼

        Gateway responde ao cliente
```

---

## Assinatura do Token

Todos os tokens são assinados utilizando criptografia assimétrica (**RS256**).

A assinatura utiliza:

- chave privada exclusiva do Token-MS;
- algoritmo RS256;
- identificador da chave (`kid`).

Exemplo de Header:

```json
{
    "alg": "RS256",
    "typ": "JWT",
    "kid": "token-v1"
}
```

O campo `kid` identifica qual chave pública deve ser utilizada durante a validação.

---

## Publicação das chaves (JWKS)

O Token-MS disponibiliza suas chaves públicas através do endpoint:

```text
GET /.well-known/jwks.json
```

Esse endpoint é público e retorna todas as chaves válidas para verificação da assinatura dos JWTs.

Exemplo:

```json
{
    "keys": [
        {
            "kty": "RSA",
            "kid": "token-v1",
            "alg": "RS256",
            "use": "sig",
            "n": "...",
            "e": "AQAB"
        }
    ]
}
```

O endpoint suporta múltiplas chaves simultaneamente, permitindo futuras rotações de chave sem interromper a validação dos tokens emitidos.

---

## Fluxo de validação

Os sistemas consumidores devem validar os tokens seguindo o fluxo abaixo.

```text
Receber JWT

      │

      ▼

Ler o Header

      │

      ▼

Obter o campo "kid"

      │

      ▼

Consultar o endpoint JWKS

      │

      ▼

Selecionar a chave pública

      │

      ▼

Validar assinatura RS256

      │

      ▼

Validar expiração

      │

      ▼

Consumir as claims
```

A chave privada permanece exclusivamente no Token-MS e nunca deve ser compartilhada com sistemas consumidores.

---

## Claims do Token

O Token JWT Enriquecido reúne informações provenientes do Keycloak e das projeções mantidas pelo Token-MS.

| Claim | Origem |
|--------|--------|
| `sub`, `preferred_username`, `email` | Keycloak |
| `rf`, `cpf` | Keycloak (sobrescritos pela projeção do Token-MS, quando disponível) |
| `nome`, `situacao`, `dre_codigo`, `contrato_externo` | Token-MS |
| `perfis`, `permissoes` | Token-MS |
| `perfilSelecionado` | Informado quando um perfil é selecionado durante a emissão do token |
| `iss` | Emissor do token |
| `iat`, `exp` | Emissão e expiração |

Caso não exista projeção para o usuário, os atributos provenientes do Token-MS poderão estar ausentes ou conter listas vazias.

---

## Endpoints

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| `POST` | `/identidade-token/api/v1/token/enriquecido/{usuario_id}` | Gera um novo Token JWT Enriquecido. |
| `POST` | `/identidade-token/api/v1/token/validar/` | Valida a assinatura, integridade e expiração do token. |
| `GET` | `/identidade-token/.well-known/jwks.json` | Publica o conjunto de chaves públicas (JWKS). |

---

## Resumo do fluxo

1. O usuário é autenticado pelo Keycloak.
2. O Gateway solicita ao Token-MS a emissão do Token JWT Enriquecido.
3. O Token-MS consulta as projeções do usuário.
4. O Token-MS compõe as claims e assina o JWT utilizando RS256.
5. O Gateway devolve o token ao cliente.
6. Os sistemas consumidores validam o JWT utilizando o endpoint JWKS antes de consumir suas claims.
