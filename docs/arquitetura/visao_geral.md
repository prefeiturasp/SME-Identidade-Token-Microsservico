# Visão Geral

## Objetivo

O **SME-Identidade-Token-Microsservico** é responsável por compor, enriquecer e disponibilizar atributos complementares de autorização utilizados pelos sistemas da Secretaria Municipal de Educação de São Paulo (SME-SP).

O serviço atua como uma camada complementar ao Keycloak, centralizando informações de autorização provenientes de diferentes fontes e disponibilizando uma projeção consistente para consumo pelos sistemas da plataforma.

Seu principal objetivo é desacoplar regras de autorização, projeções legadas e atributos corporativos do provedor de identidade, permitindo que esses dados evoluam independentemente do processo de autenticação.

## Papel na arquitetura

O Keycloak permanece como a autoridade responsável pela identidade, autenticação e protocolos de segurança da plataforma.

O SME-Identidade-Token-Microsservico complementa esse processo, sendo responsável por:

- manter projeções de autorização;
- consolidar perfis e permissões;
- compor atributos complementares (claims);
- compor o token JWT enriquecido;
- assinar os tokens utilizando RS256;
- publicar as chaves públicas por meio do endpoint JWKS;
- disponibilizar projeções para consumo pelos serviços da plataforma;
- preservar compatibilidade com sistemas legados.

Dessa forma, o serviço separa claramente as responsabilidades entre autenticação e autorização complementar.

## Fluxo

```text
                   +----------------+
                   |   Keycloak     |
                   | Identidade     |
                   +-------+--------+
                           |
                           | Identidade base
                           |
                           ▼
                 +-------------------------+
                 | SME Identidade Token    |
                 |                         |
                 | • Projeções             |
                 | • Perfis                |
                 | • Permissões            |
                 | • Claims                |
                 | • JWT Enriquecido       |
                 | • JWKS                  |
                 +-----------+-------------+
                             |
          +------------------+------------------+
          |                                     |
          ▼                                     ▼
  Auth Gateway                      Sistemas consumidores
```

## Principais responsabilidades

O serviço possui as seguintes responsabilidades:

- sincronizar projeções de autorização recebidas de sistemas externos;
- persistir perfis, permissões e demais atributos de autorização;
- disponibilizar consultas sobre as projeções armazenadas;
- compor o token JWT enriquecido;
- assinar os tokens utilizando RS256;
- publicar as chaves públicas por meio do endpoint JWKS;
- enriquecer informações utilizadas durante a composição de tokens;
- reduzir o acoplamento entre os sistemas consumidores e o provedor de identidade.

## Limites de responsabilidade

O SME-Identidade-Token-Microsservico **não** é responsável por:

- autenticar usuários;
- validar credenciais;
- emitir identidade oficial;
- gerenciar sessões;
- substituir o Keycloak como Identity Provider (IdP).

Essas responsabilidades permanecem sob domínio do Keycloak.

## Domínios da aplicação

A aplicação está organizada em domínios funcionais.

| Domínio | Responsabilidade |
|---------|------------------|
| Core | Endpoints de infraestrutura e funcionalidades comuns da aplicação. |
| Autenticação | Proteção dos endpoints por meio de autenticação via API Key. |
| Perfil | Gerenciamento das projeções de usuários, perfis e permissões utilizadas na composição dos atributos de autorização. |
| Tokens | Emissão, validação e publicação dos tokens JWT enriquecidos e gerenciamento das chaves de assinatura. |
