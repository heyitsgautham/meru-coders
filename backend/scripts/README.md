# Backend scripts

| Folder or file | What it is |
|---|---|
| `build_*.py`, `merge_chandas_datasets.py`, `fill_missing_gana.py` | Build or repair the CSV datasets under `backend/data/` and `backend/source/` |
| `import_chandas_data.py`, `import_ganesh_matra.py`, `consolidate_matra.py`, `merge_meter_data.py` | One-off importers that produced the meter CSVs in `backend/data/`; `import_chandas_data.py` reads a sanskrit-coders/chandas clone under `repos/` |
| `install_tts.sh` | Installs the optional local Sanskrit TTS model stack |
| `build_vector_db.py` | Rebuild the ChromaDB index in `backend/data/chroma_db/` for the RAG chatbot; needs the `rag` extra |
| `*.sql`, `*supabase*.py`, `*community_tables.py`, `add_password_hash_*.py` | One-off Supabase schema setup and migrations; they read credentials from the environment |
| `smoke/` | Scripts that call a running backend on `localhost:5000`; start it with `uv run python backend/run.py` first |
| `manual/` | Exploratory scripts from development, such as TTS voice checks and pada splitting experiments |

Run a script as a module from the repository root, for example `uv run python -m backend.scripts.merge_meter_data`.
None of these run in CI, but `backend/tests/test_harness_imports.py` checks that their imports of backend code resolve.
The offline test suite is `backend/tests/`, run with `uv run pytest`.
