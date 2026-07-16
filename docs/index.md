# SME Identidade Token Microsserviço

Documentação técnica do serviço de identidade responsável pela agregação de atributos, composição de autorização e emissão de tokens enriquecidos para o ecossistema SME.

O microsserviço atua como camada complementar ao Keycloak, desacoplando informações de identidade específicas do domínio de negócio do provedor de autenticação. Sua função é consolidar atributos distribuídos, compor permissões efetivas, enriquecer claims de segurança e disponibilizar representações de identidade compatíveis com diferentes consumidores da plataforma.

Além da emissão de tokens enriquecidos, o serviço gerencia a persistência de atributos complementares, a projeção de modelos de autorização, a interoperabilidade com sistemas legados e os fluxos operacionais relacionados ao ciclo de vida de refresh tokens.

```{toctree}
:maxdepth: 2
:caption: Conteúdo

arquitetura/visao_geral
controle/index
api
```
