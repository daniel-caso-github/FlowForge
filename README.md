# FlowForge

Temporal-saga-based accounts-payable invoice processing platform, covering the Peru (PE) and Spain (ES) jurisdictions.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker + Docker Compose (only needed for the local saga demo stack, not for tests)

## Setup

```bash
uv sync --all-extras --all-packages
```

This creates a `.venv/` at the repo root (uv-managed, Python 3.12+) with every workspace member's dependencies installed (`libs/contracts`, `libs/jurisdiction-packs`, `datagen`, `worker`, `services/budget`, `services/external-sim`). `--all-packages` is required — without it, `uv sync` only installs the root project's dependencies, not the workspace members'. `uv run` invokes commands against the venv automatically, so activating it manually is optional:

```bash
source .venv/bin/activate   # optional — uv run does this implicitly
```

## Running tests

```bash
uv run --all-extras pytest
```

Lint and type-check:

```bash
uv run --all-extras ruff check .
uv run --all-extras mypy .
```

Or via the Taskfile:

```bash
task test
task lint
```

Tests run locally against a `uv`-managed virtual environment (`.venv/`) — no Docker required. CI runs the same commands.

To run a single workspace package:

```bash
uv run --all-extras --package datagen pytest
```

## Configuration

No environment setup is required to run the test suite — it uses local defaults (SQLite, `localhost` URLs) and has no external dependencies.

Environment variables (all optional, only relevant when running services outside Docker Compose — the demo stack below sets them automatically):

| Variable | Default | Used by |
|---|---|---|
| `BUDGET_DATABASE_URL` | `sqlite:///./budget.db` | `budget-service` |
| `BUDGET_SERVICE_URL` | `http://localhost:8001` | `worker` |
| `EXTERNAL_SIM_URL` | `http://localhost:8002` | `worker` |
| `TEMPORAL_ADDRESS` | `localhost:7233` | `worker` |

## Local demo stack (optional)

Starts Temporal, Postgres, and the FastAPI services via Docker Compose:

```bash
task up    # start
task down  # stop
```

## Project structure

- `libs/contracts` — shared value objects and canonical invoice/credit-note contracts
- `libs/jurisdiction-packs` — PE/ES tax-ID validation, bank-account validation, and UBL/Facturae XML parsing
- `datagen` — synthetic dataset generator (ground-truth invoices, degradation, scenario injection)
- `worker` — Temporal workflows and activities (saga orchestration)
- `services/budget`, `services/external-sim` — FastAPI services
- `data/v0.1` — generated synthetic dataset
