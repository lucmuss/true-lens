# Deployment and Ops

## Runtime placement
- Repository: `/srv/projects/web/recruiter-candidate-hub` (TrueLens)
- Deployment target stack: `/srv/docker/apps-stack`

## Baseline services
- `true_lens-web`
- `true_lens-nginx`
- shared postgres (apps-stack)

## Required checks
- `docker compose config --quiet`
- `/healthz/` HTTP 200
- database migrations successful
- screenshots generated to `output/gui-screenshots/`

## Env-driven controls
All limits/timeouts/prices configurable via `.env`:
- step timeout seconds
- profile view window seconds
- lookup per day limits
- vote cooldown days
- vote retention years
- credit price per unit
- coordinator election timeout
- replication factor
