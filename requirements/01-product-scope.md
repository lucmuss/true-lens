# Product Scope

## Goal
A secure recruiter platform for profile discovery by multi-step identity confirmation.

## Primary user roles
- Anonymous visitor: can solve captcha, do one free lookup per day.
- Recruiter (authenticated): can do lookup + voting + credit purchase + settings.
- Admin: moderation, node management, audits, financial overview.

## Main product modules
1. Landing page with hard captcha gate.
2. Multi-step profile lookup workflow.
3. Candidate profile view with privacy masking.
4. Attribute voting system with recruiter constraints.
5. Credit economy and Stripe checkout.
6. Account system (registration, verification, login, password reset).
7. Security guardrails (rate limits, bans, step timeouts, anti-bot token checks).
8. Replication subsystem (coordinator + backup coordinator + replica).
9. Admin control center for replication and moderation.
