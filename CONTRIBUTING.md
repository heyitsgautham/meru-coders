# Contributing

Meru Coders started as the Smart India Hackathon 2025 project of team Meru Coders.
This guide covers how to set up, change and check the code.

## Set up

```bash
uv sync                      # backend virtualenv from uv.lock, with the dev tools
cd frontend && npm ci        # frontend packages from package-lock.json
```

Copy `.env.example` to `.env` and `frontend/.env.example` to `frontend/.env` only for the features you need.
A new environment variable goes into one of those two example files in the same commit, or `test_env_example.py` fails.
Never commit either `.env` file, service account JSON, or any key.
CI runs gitleaks on every push and fails on a committed secret.

## Make a change

1. Branch from `main`.
2. Keep each commit to one change, and land behavior changes with the tests that prove them.
3. Run the checks below before you push.
4. Open a pull request against `main`; CI must be green before it merges.

## Checks

Backend, from the repository root:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov
```

Frontend, from `frontend/`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

`uv run ruff format .` fixes formatting.
The coverage floor sits in `pyproject.toml` under `[tool.coverage.report]`; raise it when you add tests, never lower it.

## Where tests go

| Kind | Location | Runs in CI |
|---|---|---|
| Unit and API tests that need no network or keys | `backend/tests/test_*.py` | yes |
| Frontend unit tests | `frontend/src/**/*.test.ts(x)` | yes |
| Corpus accuracy runs and engine comparisons | `backend/evaluation/` | no |
| Scripts that call a running server | `backend/scripts/smoke/` | no |

Use the fixtures in `backend/tests/conftest.py`.
`chanda` is one shared meter engine, and `app` and `client` give you the Flask app without Supabase.

When you change the meter engine, `uv run pytest -m corpus` checks the accuracy floors, and `uv run python -m backend.evaluation.csv_accuracy --all -v` lists every miss.

## Dependencies

Add Python packages with `uv add <package>` (or `uv add --optional rag <package>` for the retrieval stack), then refresh the Docker requirements file:

```bash
uv export --frozen --no-hashes --no-dev --extra rag --no-emit-project -o backend/requirements.txt
```

Add frontend packages with `npm install` inside `frontend/` and commit `package-lock.json`.
Dependabot opens weekly update pull requests for both.

## Commit messages

Use `type(scope): subject` in the imperative, under 72 characters, for example `fix(auth): make the local login fallback work without Supabase`.
Types are `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `style`, `perf` and `chore`.
Put the reason for the change in the body.
