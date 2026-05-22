# API Contract (Initial)

## Public flow APIs
- `POST /api/security/captcha/start`
- `POST /api/security/captcha/verify`
- `POST /api/search/start`
- `POST /api/search/step/{n}`
- `GET /api/search/session/{token}/status`
- `GET /api/search/session/{token}/profile`

## Vote APIs
- `POST /api/candidates/{id}/vote`
- `GET /api/candidates/{id}/votes`

## Credits APIs
- `POST /api/credits/checkout`
- `POST /api/credits/webhook/stripe`
- `GET /api/credits/wallet`

## Enrichment APIs
- `POST /api/candidates/{id}/enrichment`
- `GET /api/moderation/queue`
- `POST /api/moderation/queue/{id}/approve`
- `POST /api/moderation/queue/{id}/reject`

## Replication APIs (internal)
- `POST /api/internal/replication/push`
- `POST /api/internal/replication/ack`
- `POST /api/internal/heartbeat`
- `POST /api/internal/election`

## Security requirements
- JS challenge token required on every API call.
- CSRF for browser state-changing requests.
- Internal replication endpoints require mTLS or signed HMAC headers.
