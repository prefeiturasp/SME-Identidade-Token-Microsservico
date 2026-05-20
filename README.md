# SME-Identidade-Token-Microsservico

Microsserviço de enriquecimento de claims e Token Exchange (RFC 8693).

É chamado por:

* **etl-ms** — envia lotes via `POST /api/v1/etl/push-batch` (após carregar o
  Keycloak, envia atributos complementares).
* **gateway-ms** — consulta `GET /api/v1/users/{login}/claims` para enriquecer
  os bodies dos endpoints OIDC e legado.
* **Sistemas autorizados** — `POST /api/v1/token/exchange/` para trocar
  tokens (RFC 8693) usando o Keycloak.

## Autenticação interna

Todos os endpoints (exceto `/api/health/*`) exigem o header configurado em
`INTERNAL_TOKEN_HEADER` (default `X-Internal-Token`). Em desenvolvimento o
valor padrão é `dev-internal-token`.

## Rodar localmente

```bash
cp .env.example .env
docker compose up -d
curl -s http://localhost:8003/api/health/
curl -s http://localhost:8003/api/docs/
```

## Testes

```bash
pip install -r requirements.txt
python manage.py migrate --settings=token_ms.settings_test || true
pytest
# 22 testes, cobertura ~98%
```

## Endpoints

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| GET  | `/api/health/` | liveness |
| GET  | `/api/health/ready/` | readiness |
| POST | `/api/v1/etl/push-batch` | recebe lote do etl-ms |
| GET  | `/api/v1/users/{login}/claims` | claims com cache (KeyDB) |
| GET  | `/api/v1/admin/claims/` | listagem (filtros por source, tipo, exec_id) |
| GET  | `/api/v1/admin/claims/{login}/` | detalhe |
| POST | `/api/v1/admin/claims/{login}/invalidate-cache/` | invalida cache |
| GET  | `/api/v1/admin/etl-logs/` | auditoria dos lotes recebidos |
| POST | `/api/v1/token/exchange/` | Token Exchange (RFC 8693) |
