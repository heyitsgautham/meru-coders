# Backend scripts

| Folder or file | What it is |
|---|---|
| `build_*.py`, `merge_chandas_datasets.py`, `fill_missing_gana.py` | Build or repair the CSV datasets under `backend/data/` and `backend/source/` |
| `build_vector_db.py` | Rebuild the ChromaDB index in `backend/data/chroma_db/` for the RAG chatbot; needs the `rag` extra |
| `*.sql`, `*supabase*.py`, `*community_tables.py`, `add_password_hash_*.py` | One-off Supabase schema setup and migrations; they read credentials from the environment |
| `smoke/` | Scripts that call a running backend on `localhost:5000`; start it with `uv run python backend/run.py` first |
| `manual/` | Exploratory scripts from development, such as TTS voice checks and pada splitting experiments |

None of these run in CI.
The offline test suite is `backend/tests/`, run with `uv run pytest`.
