# Modelos

Esta seção descreve os modelos persistidos pelo **SME-Identidade-Token-Microsservico**, responsáveis por armazenar a projeção de autorização dos usuários e os atributos complementares publicados pelo ETL.

Os modelos representam as informações utilizadas para compor e disponibilizar atributos de autorização consumidos pelos sistemas da plataforma.

## Relacionamento entre os modelos

```text
ProjecaoUsuario
        │
        ├──────────► PerfilUsuario
        │
        └──────────► ModuloPermissaoUsuario

AtributoComplementarUsuario (associado a ProjecaoUsuario por RF/CPF)
        │
        └──────────► VinculoAtributoComplementar
```

Cada usuário possui uma projeção de autorização, composta por seus perfis e permissões. Separadamente, o ETL publica atributos complementares (identidade e vínculos funcionais) que se associam à projeção de forma oportunista, quando ela existe.

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

# ModuloPermissaoUsuario

Representa uma permissão CRUD concedida a um usuário para um módulo de um sistema.

A permissão é concedida por sistema e módulo, com quatro ações independentes — a granularidade real é (sistema, módulo, ação), não um código de permissão único. A unicidade é sempre pelo par `(sistema_id, modulo_id)`, já que `modulo_id` sozinho pode se repetir entre sistemas diferentes.

## Campos da permissão

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único da permissão. |
| `usuario` | FK | Referência para a projeção do usuário. |
| `sistema_id` | Integer | Identificador do sistema. |
| `sistema_nome` | String | Nome do sistema. |
| `modulo_id` | Integer | Identificador do módulo (único apenas em conjunto com `sistema_id`). |
| `modulo_nome` | String | Nome do módulo. |
| `consultar` | Boolean | Permissão de consulta no módulo. |
| `inserir` | Boolean | Permissão de inserção no módulo. |
| `alterar` | Boolean | Permissão de alteração no módulo. |
| `excluir` | Boolean | Permissão de exclusão no módulo. |

---

# AtributoComplementarUsuario

Registra os atributos complementares de um usuário, publicados em lote pelo ETL (endpoint `etl/push-batch`) a partir das fontes legadas.

Identifica o usuário por RF, CPF ou matrícula. O payload de origem não carrega o identificador do usuário na plataforma, então o vínculo com `ProjecaoUsuario` é resolvido de forma oportunista (por RF ou CPF) e pode ficar nulo até essa projeção existir.

## Campos do atributo complementar

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único do registro. |
| `usuario` | FK (opcional) | Referência para a projeção do usuário, quando resolvida. |
| `rf`, `cpf`, `matricula` | String | Identificadores naturais do usuário na origem. |
| `nome`, `email` | String | Dados de identidade. |
| `tipo_usuario` | String | Tipo inferido a partir da fonte (servidor, aluno, terceiro). |
| `cargo`, `funcao`, `unidade`, `unidade_codigo`, `dre`, `ue` | String | Atributos escalares de outros tipos de usuário (ex.: aluno) — para servidor, esse dado vem de `vinculos`, não desses campos. |
| `cod_escola`, `turma` | String | Atributos específicos de aluno. |
| `tipo_acesso` | String | Atributo específico de terceiro. |
| `situacao`, `fonte`, `id_execucao` | String/UUID | Metadados de origem e execução do ETL. |
| `criado_em`, `atualizado_em` | DateTime | Datas de controle do registro. |

---

# VinculoAtributoComplementar

Representa um vínculo funcional vigente de um servidor (cargo base, cargo sobreposto/comissionado ou função/atividade).

Um servidor pode ter múltiplos vínculos simultâneos e independentes — inclusive mais de um cargo base ao mesmo tempo — cada um com seu próprio cargo e sua própria unidade/DRE, por isso é modelado como tabela filha de `AtributoComplementarUsuario` (1 atributo → N vínculos), não como campos escalares. A chave `(atributo, tipo_vinculo, codigo_vinculo_origem)` é única, usada para upsert idempotente nos reenvios do ETL.

## Campos do vínculo

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único do vínculo. |
| `atributo` | FK | Referência para o atributo complementar do usuário. |
| `tipo_vinculo` | String | Tipo do vínculo: `cargo_base`, `cargo_sobreposto` ou `funcao_atividade`. |
| `codigo_vinculo_origem` | String | Chave natural do vínculo na origem, usada para upsert idempotente. |
| `cargo_codigo`, `cargo_nome` | String | Identificação do cargo. |
| `unidade_codigo`, `unidade_nome` | String | Identificação da unidade de lotação do vínculo. |
| `dre_codigo` | String | Código da DRE responsável pela unidade do vínculo. |
| `situacao` | String | Situação do vínculo, quando disponível na origem. |
| `data_inicio` | String | Data de início do vínculo, quando disponível na origem. |
| `vigente` | Boolean | Indica se o vínculo está vigente. |
| `criado_em`, `atualizado_em` | DateTime | Datas de controle do registro. |
