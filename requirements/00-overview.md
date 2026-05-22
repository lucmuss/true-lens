# Requirements Overview

This folder is the single planning baseline for the initial implementation.

## Included specifications
1. `01-product-scope.md`
2. `02-user-flows.md`
3. `03-security-model.md`
4. `04-data-model.md`
5. `05-api-contract.md`
6. `06-distributed-architecture.md`
7. `07-deployment-and-ops.md`

## Implementation principles
- API-first and HTMX/AJAX-first UX.
- Security controls server-side first; frontend checks are only auxiliary.
- PostgreSQL-only persistence.
- Configurable behavior through environment variables and JSON config files.
