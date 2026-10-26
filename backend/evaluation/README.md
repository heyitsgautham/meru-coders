# Evaluation harnesses

These scripts measure how well the meter engine does on real corpora, and compare it with other implementations.
The accuracy figures the project publishes are asserted, not just printed.

| Figure | Asserted by | Floor |
|---|---|---|
| Classical benchmark, four measures | `backend/tests/test_corpus_accuracy.py`, and `csv_accuracy` exits 1 below it | 146 first lines, 134 every-line verses, 485 lines, 139 whole verses (94.6%) |
| Rigveda, exact and accepted meter | the same test, and `rigveda_validation` exits 1 below it | 8,067 exact, 9,009 accepted |
| Regression verses (Gāyatrī, three Gita verses, two fragments) | `backend/tests/test_regression_verses.py`, which replaced `all_fixes.py` | all pass; the Jagatī case is an expected failure |

The floors live in `backend/pipeline/benchmarks.py` with the scoring rules, and CI runs the corpus tests in the Data quality job.
The other scripts here are exploratory comparisons that print reports; several call Gemini or need the IITK, GPT and ICU baselines in `reference/alternative_implementations/`.

Every harness imports the backend as a package, so run it as a module from the repository root:

```bash
uv run python -m backend.evaluation.csv_accuracy --all -v    # 147-verse classical benchmark
uv run python -m backend.evaluation.rigveda_validation -v    # 9,247 labelled Rigveda riks
uv run pytest -m corpus                                      # the same figures as assertions
```

| Group | Files |
|---|---|
| Corpus accuracy | `csv_accuracy.py`, `csv_line_level.py`, `csv_verse_level.py`, `rigveda_validation.py`, `ramayana_validation.py`, `wsc2023_validation.py`, `true_vedic_accuracy.py`, `autodetect_accuracy.py` |
| Comparisons with other engines | `definitive_comparison.py`, `comprehensive_comparison.py`, `cross_dataset_comparison.py`, `model_comparison.py`, `performance_comparison.py`, `sanskrit_repo_comparison.py`, `compare_*.py` |
| LLM baselines | `llm_chanda_prediction.py`, `rigveda_prediction.py`, `run_gpt_tests.py`, `chanda_gpt_adapter.py` |
| Fixture data | `data/` holds the Rigveda verse sets that `backend/scripts/build_rigveda_dataset.py` and `build_complete_verses.py` generate |

The Markdown files beside them are the reports those runs produced during the hackathon.

Comparisons with the original IITK engine and the sanskrit-coders repositories expect those clones under `repos/` at the repository root, the only place a harness still adds to `sys.path`.
`backend/tests/test_harness_imports.py` checks that every first-party import in this directory and in `backend/scripts/` resolves, so a renamed module breaks CI instead of the next manual run.
