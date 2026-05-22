# Security Model

## Core controls
1. JavaScript-required challenge token tied to IP + UA + short TTL.
2. Captcha gate (self-hosted Python captcha library, no external captcha provider).
3. Django rate limits on all sensitive endpoints.
4. Per-IP daily lookup cap for anonymous users.
5. Per-account daily/weekly caps for recruiters.
6. Server-side step timer state in signed session records.
7. Progressive IP penalty and ban table.
8. Strict CSRF, secure cookies, HSTS (prod), CSP.
9. Login alert email on successful authentication.
10. Argon2 password hasher + strong password policy (>=12 chars + special char).

## Anti-extraction controls
- No bulk-list endpoint for candidates.
- Only one resolved profile per allowed lookup.
- Lookup token invalidated after successful reveal.
- Response jitter and fixed-size partial errors to reduce oracle quality.
- Optional opaque request signature based on rotating server nonce.

## Privacy controls
- Masked output by default.
- Recruiter identity hidden in frontend/API public responses.
- Anonymous vote option strips recruiter linkage from outward reads.
- Retention policy for vote aging (default 5 years), excluded from public aggregates after expiry.

## Abuse handling
- `SecurityEvent` audit model for suspicious traffic.
- `IPBan` with reason, expiry, and escalating cooldown logic.
- Admin override endpoints.
