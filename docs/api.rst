Referência de código
======================

Esta página publica as docstrings dos principais módulos do projeto. Detalhes
de endpoints, status HTTP e contratos externos devem permanecer no OpenAPI ou
em páginas técnicas específicas.

Core
-------

.. automodule:: apps.core.api.views
   :members:

.. automodule:: apps.core.api.serializers
   :members:

.. automodule:: apps.core.api.urls
   :members:

Autenticação
---------------

.. automodule:: apps.autenticacao.api.autenticacao
   :members:

Perfil
---------

.. automodule:: apps.perfil.models
   :members:

.. automodule:: apps.perfil.api.views
   :members:

.. automodule:: apps.perfil.api.serializers
   :members:

.. automodule:: apps.perfil.api.urls
   :members:

Recuperação de senha
--------------------

.. autoclass:: apps.recuperacao_senha.dtos.UsuarioIdentidade

.. automodule:: apps.recuperacao_senha.models
   :members:

.. automodule:: apps.recuperacao_senha.services.recuperacao_senha
   :members:

.. automodule:: apps.recuperacao_senha.api.views
   :members:

.. automodule:: apps.recuperacao_senha.services.sistemas
   :members:

.. automodule:: apps.recuperacao_senha.api.serializers
   :members:

Cache
--------

.. automodule:: apps.cache.chaves
   :members:

.. automodule:: apps.cache.services
   :members:

Tokens
---------

.. automodule:: apps.tokens.services
   :members:

.. automodule:: apps.tokens.token_enriquecido
   :members:

.. automodule:: apps.tokens.libs.jwt_chaves
   :members:
   :no-index:

.. automodule:: apps.tokens.libs.jwt_validacao
   :members:

.. automodule:: apps.tokens.libs.jwks
   :members:

.. automodule:: apps.tokens.api.views
   :members:

.. automodule:: apps.tokens.api.serializers
   :members:

.. automodule:: apps.tokens.api.urls
   :members:
