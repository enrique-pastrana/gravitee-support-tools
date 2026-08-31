# Reproduction environment — TICKET-{{ticket_id}}

## Target (customer's setup)

- Product / version: {{product}} {{version}}
- Database: …
- Other services: …
- Load profile: …
- Relevant config: …

## Local setup

- OS / machine: macOS, Apple Silicon, 16 GB RAM
- Containers / VMs: … (none for a browser/UI-only repro)
- Tooling: docker, docker compose, k6, … — or, for a UI/layout repro, just the
  browser (name + version) and the viewport/resolution
- URL under test (UI repro): …

## Bring up

```bash
# Stack repro: commands to start the services
# Browser/UI repro: no stack — open the URL above at the noted viewport
```

## Tear down

```bash
docker compose down -v   # stack repro only; nothing to tear down for a browser repro
```

## Notes

- Resource footprint
- Caveats / known differences vs. customer setup
