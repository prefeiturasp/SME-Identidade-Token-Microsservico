# Modelos

Esta seção descreve os modelos persistidos pelo **SME-Identidade-Token-Microsservico**, responsáveis por armazenar a projeção de autorização dos usuários.

Os modelos representam as informações utilizadas para compor e disponibilizar atributos de autorização consumidos pelos sistemas da plataforma.

## Relacionamento entre os modelos

```text
ProjecaoUsuario
        │
        ├──────────► PerfilUsuario
        │
        └──────────► PermissaoUsuario
```

Cada usuário possui uma projeção de autorização, composta por seus perfis e permissões.

---

# ProjecaoUsuario

Representa a projeção de autorização de um usuário.

Este modelo centraliza as informações cadastrais e de autorização utilizadas pelos sistemas consumidores durante a composição de claims e demais atributos complementares.

## Campos da projeção

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `usuario_id` | UUID | Identificador único do usuário. |
| `login` | String | Login do usuário na plataforma. |
| `rf` | String | Registro funcional do usuário, quando aplicável. |
| `nome` | String | Nome completo do usuário. |
| `cpf` | String | CPF do usuário. |
| `email` | String | Endereço de e-mail do usuário. |
| `situacao` | String | Situação atual do usuário. |
| `dre_codigo` | String | Código da Diretoria Regional de Educação (DRE) associada ao usuário. |
| `contrato_externo` | Boolean | Indica se o usuário possui contrato externo. |
| `criado_em` | DateTime | Data de criação do registro. |
| `atualizado_em` | DateTime | Data da última atualização do registro. |

---

# PerfilUsuario

Representa um perfil atribuído a um usuário.

Cada perfil identifica um contexto de atuação ou papel desempenhado pelo usuário dentro da plataforma.

## Campos do perfil

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único do perfil. |
| `usuario` | FK | Referência para a projeção do usuário. |
| `nome` | String | Nome do perfil. |
| `ativo` | Boolean | Indica se o perfil está ativo. |

---

# PermissaoUsuario

Representa uma permissão concedida a um usuário.

As permissões definem as operações autorizadas para determinado usuário e complementam os perfis atribuídos.

## Campos da permissão

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único da permissão. |
| `usuario` | FK | Referência para a projeção do usuário. |
| `codigo` | Integer | Código identificador da permissão. |
| `descricao` | String | Descrição da permissão. |
