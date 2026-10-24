# Evaluation harnesses

These scripts measure how well the meter engine does on real corpora, and compare it with other implementations.
They print reports instead of asserting, and several of them call Gemini or need the IITK, GPT and ICU baselines in `reference/alternative_implementations/`.
That is why they live here and not in `backend/tests/`, which holds the offline pytest suite that CI runs.

Run one from the repository root, for example:

```bash
uv run python backend/evaluation/csv_accuracy.py
uv run python backend/evaluation/rigveda_validation.py
```

| Group | Files |
|---|---|
| Corpus accuracy | `csv_accuracy.py`, `csv_line_level.py`, `csv_verse_level.py`, `rigveda_validation.py`, `ramayana_validation.py`, `wsc2023_validation.py`, `true_vedic_accuracy.py`, `autodetect_accuracy.py` |
| Comparisons with other engines | `definitive_comparison.py`, `comprehensive_comparison.py`, `cross_dataset_comparison.py`, `model_comparison.py`, `performance_comparison.py`, `sanskrit_repo_comparison.py`, `compare_*.py` |
| LLM baselines | `llm_chanda_prediction.py`, `rigveda_prediction.py`, `run_gpt_tests.py`, `chanda_gpt_adapter.py` |
| Fixture data | `data/` holds the Rigveda verse sets that `backend/scripts/build_rigveda_dataset.py` and `build_complete_verses.py` generate |

The Markdown files beside them are the reports those runs produced during the hackathon.
