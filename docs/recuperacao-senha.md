# Recuperação de senha

## Objetivo

Gerenciar as solicitações de recuperação, as regras de senha e o envio de
e-mail para o contrato legado publicado pelo Gateway. O MS-Identidade
corresponde a este MS-Token e utiliza a base já configurada por
`IDENTIDADE_TOKEN_DB_URL`.

O Gateway consulta a conta e altera a credencial no provedor de identidade.
O MS-Token recebe os dados normalizados e a confirmação do resultado por
chamadas autenticadas. Não acessa o provedor nem precisa de seu SDK,
endereço ou credenciais administrativas.

## Integração com o Gateway

A conta é representada por `UsuarioIdentidade`, definido em
`apps.recuperacao_senha.dtos`, com identificador, login, nome,
e-mail, situação, RF e CPF. O contexto identifica o conjunto de contas
informado pelo Gateway.

Somente o Gateway consulta a conta atual e fornece esses dados. O
consumidor das rotas públicas não escolhe a conta, o contexto ou o
resultado da alteração. O MS-Token não faz chamadas de retorno ao Gateway.

## Operações de recuperação

As rotas internas exigem a API Key do serviço, configurada por `API_KEY`
e enviada no cabeçalho `API_KEY_HEADER` (`X-API-Key` por padrão).
O prefixo é `/identidade-token/api/v1/recuperacao-senha/`.
Todas recebem objetos JSON; os contratos públicos legados permanecem no Gateway.

| Método | Sufixo | Entrada | Sucesso |
| --- | --- | --- | --- |
| `POST` | `solicitacoes` | `contexto`, `login`, `sistema` e `conta` (ou `null` para usuário ausente). | `200`, com o e-mail como string JSON. |
| `POST` | `tokens/validar` | `contexto` e `token`. | `200`, com um booleano JSON. |
| `POST` | `alteracoes/consultar` | `contexto` e `token`. | `200`, com `usuario_id` e `login`. |
| `POST` | `alteracoes/reservar` | `contexto`, `token`, `senha`, `conta` atual e `operacao_id` (UUID gerado pelo Gateway). | `200`, com `operacao_id`, `usuario_id` e `login`. |
| `POST` | `alteracoes/concluir` | `contexto`, `operacao_id`, `resultado` e `motivo` opcional. | `200`, com o login quando o resultado for sucesso. |

A reserva valida o token e a senha antes de autorizar a alteração no
provedor. A senha é usada em memória e não é persistida.

Na conclusão, `resultado` aceita `sucesso`, `rejeitada` ou `incerta`.
Os motivos de rejeição são `historico`, `padrao`, `politica`,
`indisponivel` e `conta`. Rejeições e resultados incertos são
registrados antes da resposta de erro.

## Fluxo

1. O Gateway consulta o login exato e envia a conta normalizada ao MS-Token.
2. O MS-Token valida o sistema e o e-mail, gera um UUID e substitui a
   solicitação anterior da mesma conta.
3. O MS-Token envia o modelo HTML do legado com nome, login e link formado
   pela página do sistema seguida do UUID.
4. A consulta de validade usa somente os registros locais, sem consumir o código.
5. Na troca, o Gateway consulta a identidade vinculada ao token no MS-Token
   e obtém a conta atual no provedor.
6. O MS-Token valida prazo, conta habilitada e regras de senha, e reserva
   o uso do token para uma operação.
7. O Gateway verifica o histórico e altera a senha no provedor.
8. O Gateway confirma o resultado ao MS-Token. Após sucesso, o MS-Token
   invalida o código e retorna o login.

A validade é de seis horas. Há uma solicitação por combinação de contexto
e conta, independentemente do sistema usado para solicitá-la.

### Regras da senha

A senha deve conter de 8 a 12 caracteres, sem espaços, com pelo menos uma
letra maiúscula, uma minúscula e um número ou caractere especial aceito
pelo legado. As senhas padrão de SGP e Plateia são rejeitadas.

O Gateway verifica a configuração do histórico mínimo de cinco senhas e
traduz a rejeição do provedor para o resultado de negócio. O MS-Token
não consulta nem armazena esse histórico.

### Falhas durante a alteração

A reserva é gravada antes da chamada de alteração da credencial. Enquanto
ela existir, o token não permite outra tentativa. Uma rejeição confirmada
libera o código, desde que a solicitação ainda seja a mesma e esteja no prazo.

Ausência de confirmação ou resultado incerto mantém o código bloqueado
e exige nova solicitação. Isso também vale quando a senha foi aplicada,
mas a resposta entre os serviços foi perdida.

Repetir a reserva com o mesmo identificador retorna a mesma autorização
enquanto ela estiver vigente. Repetir uma conclusão com o mesmo resultado
retorna o resultado registrado. Confirmações conflitantes são rejeitadas.
A conclusão de uma operação antiga não altera um link solicitado depois dela.

### Respostas

| Situação | Resposta |
| --- | --- |
| Login, sistema ou e-mail indisponível na solicitação | `400`, com mensagem de negócio como string JSON |
| UUID malformado na consulta de validade | `400` |
| UUID desconhecido, expirado, reservado ou consumido na consulta | `200 false` |
| Código ou conta inválidos na reserva | `401`, com mensagem de negócio |
| Senha fora das regras, padrão ou no histórico | `401`, com mensagem de negócio |
| Campos obrigatórios ausentes | `400`, com erros por campo |
| API Key ausente ou inválida | `401` |
| Operação ausente, substituída ou confirmação conflitante | `409` |
| Falha no envio, falha informada pelo Gateway ou resultado incerto | `502` |

## Cadastro de sistemas pelo ETL

Os sistemas de recuperação são recebidos pela entrada de lote já utilizada
pelo ETL: `POST /identidade-token/api/v1/etl/push-batch`. A carga usa a API Key
existente do serviço e não possui endpoint próprio de criação ou alteração.

A seção `sistemas_recuperacao_senha` é opcional. O campo `usuarios` mantém seu
contrato e pode ser uma lista vazia quando a carga contiver somente sistemas.

```http
POST /identidade-token/api/v1/etl/push-batch HTTP/1.1
X-API-Key: <chave-do-ms-token>
Content-Type: application/json

{
  "usuarios": [],
  "sistemas_recuperacao_senha": [
    {
      "codigo_sistema": 1,
      "nome_sistema": "SGP",
      "pagina_recuperacao_senha": "https://novosgp.sme.prefeitura.sp.gov.br/redefinir-senha/"
    }
  ]
}
```

| Campo do sistema | Regra |
| --- | --- |
| `codigo_sistema` | Inteiro positivo, sem repetição na seção. Identifica o sistema no cadastro de recuperação. |
| `nome_sistema` | Nome obrigatório, com até 255 caracteres. |
| `pagina_recuperacao_senha` | URL válida, com até 500 caracteres. O UUID será concatenado ao final. |

O código de recuperação é independente do identificador de sistema do CoreSSO.
Todas as seções são validadas antes da gravação e persistidas em uma transação.
Cada tipo de dado tem seu próprio serializer e serviço de persistência.

Sistemas são criados ou atualizados pelo código. Omissões e listas vazias
não excluem registros. O envio de atributos de usuários continua funcionando
com o mesmo corpo e a mesma resposta de antes.

Exemplo de sucesso para uma carga contendo somente um sistema novo:

```json
{
  "processados": 0,
  "criados": 0,
  "atualizados": 0,
  "sistemas_recuperacao_senha": {
    "processados": 1,
    "criados": 1,
    "atualizados": 0
  }
}
```

Os totais no primeiro nível continuam correspondendo aos usuários. Os totais
de sistemas aparecem apenas quando sua seção for enviada. Reenviar um sistema
existente contabiliza uma atualização, mesmo sem alteração dos valores.

| HTTP | Comportamento |
| --- | --- |
| `200 OK` | Lote persistido; retorna os totais de usuários e das seções recebidas. |
| `400 Bad Request` | Campos inválidos ou códigos de sistema repetidos; nenhuma seção é gravada. |
| `401 Unauthorized` | API Key ausente ou inválida. |

## Persistência

| Modelo | Conteúdo |
| --- | --- |
| `SistemaRecuperacaoSenha` | Código único do sistema, nome e página de recuperação. |
| `RecuperacaoSenha` | Contexto, ID da conta, login, hash SHA-256 do UUID, expiração e identificador da reserva atual. |
| `OperacaoAlteracaoSenha` | Identificador da operação, vínculo com a solicitação, hash e login associados, estado, motivo e data de criação. |

A restrição por contexto e conta garante um único registro de recuperação
por identidade. A coluna `realm` mantém seu nome existente e recebe apenas
o contexto informado pelo Gateway. O UUID original e a senha não são persistidos.

A migração `0002` adiciona a reserva e o registro de operações. Execute
`python manage.py migrate` antes de iniciar o fluxo atualizado.

## Configuração

| Variável | Finalidade |
| --- | --- |
| `IDENTIDADE_TOKEN_DB_URL` | Base PostgreSQL do serviço, também usada pela recuperação. |
| `API_KEY` e `API_KEY_HEADER` | Autenticação das chamadas internas. |
| `EMAIL_BACKEND` | Backend de envio do Django. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` | Conexão e autenticação SMTP. |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` e `EMAIL_TIMEOUT` | Segurança e prazo da conexão de e-mail. |
| `DEFAULT_FROM_EMAIL` | Remetente das mensagens. |

Com `django.core.mail.backends.console.EmailBackend`, as versões texto e
HTML são escritas na saída da aplicação, sem envio SMTP.
