# Data pipeline

The meter engine, the API and the accuracy tests read a fixed set of committed datasets.
This page lists where each one comes from, which code reads it, and which check guards it.
Nothing here downloads data at runtime; every input is a file in the repository.

## Flow

```
external sources                     committed files                         consumers
-----------------                    ---------------                         ---------
IITK meter lists ------------------> data/chanda_*_original.csv --+
ganesh.json, vrttaratnakara.json --> data/chanda_*_imported.csv --+--> data/chanda_{sama,ardhasama,
  (import_chandas_data.py)            (merge_meter_data.py)            vishama,vedic,jaati,matra}.csv
                                                                          -> Chanda.read_data, at startup
GRETIL / Vedaweb Rigveda ----------> source/rigveda-with-meters.csv
                                       = data/rigveda_with_meters_complete.csv -> benchmarks, verse cache
                                       -> data/pragatha_pankti_verses.csv      -> golden snapshot
Rigveda_api + WSC2023 Anukramani --> evaluation/data/rigveda_authentic.py      -> evaluation harnesses
  (backend/pipeline/rigveda_dataset.py)
Gita text -------------------------> data/bhagavad_gita_verses.csv            -> golden snapshot, RAG index
Chandovallari, Vedanga lists ------> source/*.csv + source/dataset_sources.json -> /api/datasets, /api/sloka/*
```

## Datasets

| File | Origin | Read by | Guarded by |
|---|---|---|---|
| `data/chanda_sama.csv`, `chanda_ardhasama.csv`, `chanda_vishama.csv`, `chanda_vedic.csv` | curated by hand, starting from `*_original.csv` merged with `*_imported.csv` by `backend/scripts/merge_meter_data.py`; later edits mean that script no longer reproduces them, so they are sources, not build outputs | `backend/core/chanda_data.py` at startup | `backend/pipeline/meter_tables.py`, `tests/pipeline/test_data_quality.py` |
| `data/chanda_jaati.csv`, `chanda_matra.csv` | IITK lists | `backend/core/chanda_data.py` | the engine golden snapshot |
| `source/rigveda-with-meters.csv` | GRETIL and Vedaweb, one row per rk with meter, seer and deity | `/api/datasets`, the verse cache | `backend/pipeline/corpora.py` |
| `data/rigveda_with_meters_complete.csv` | built: byte-identical copy of the file above | `backend/pipeline/benchmarks.py` | `build --check` |
| `data/pragatha_pankti_verses.csv` | built: the Rigveda rows labelled Pragatha or Pankti | golden snapshot, `evaluation/pragatha_pankti_approaches.py` | `build --check` |
| `data/bhagavad_gita_verses.csv` | the Gita, one verse per row | golden snapshot, `build_vector_db.py` | `corpora.py`: no empty or repeated verse |
| `data/examples.json` | hand-picked example per meter | `/api/examples` | `corpora.py`: every meter has a verse |
| `data/page 1-47 chanda list - complete.csv` | classical verses with meter labels; the first 147 rows are verses | `backend/pipeline/benchmarks.py` | `tests/test_corpus_accuracy.py` |
| `source/dataset_sources.json` | registry of the browsable datasets | `backend/api/datasets.py`, `backend/api/verse_search.py` | `corpora.py`: every file and declared column exists |
| `evaluation/data/rigveda_authentic.py` | built from the Rigveda_api and WSC2023 clones by `backend/pipeline/rigveda_dataset.py` | `evaluation/true_vedic_accuracy.py`, `evaluation/vedic_modal.py` | `build --check`, `tests/pipeline/test_rigveda_dataset.py` |
| `data/chroma_db/` | built by `backend/scripts/build_vector_db.py` | the RAG chatbot, `rag` extra only | none; rebuild it after changing the sources |

## Building the derived datasets

One command regenerates every derived file from its committed inputs.

```bash
uv run python -m backend.pipeline.build --check            # write nothing; exit 1 if a committed file differs
uv run python -m backend.pipeline.build                    # validate the inputs, then write
uv run python -m backend.pipeline.build --repos path/to/repos   # also rebuild rigveda_authentic.py from its clones
```

| Built file | From | Rule |
|---|---|---|
| `data/rigveda_with_meters_complete.csv` | `source/rigveda-with-meters.csv` | byte copy |
| `data/pragatha_pankti_verses.csv` | the same file | the Pragātha rows, then the Paṅkti rows, each sorted by mandala as text, then sukta and rik as numbers |
| `evaluation/data/rigveda_authentic.py` | Rigveda_api and WSC2023 clones | see the last section |

Every builder is a pure function of its inputs with fixed ordering and CRLF CSV line endings.
A second build writes the same bytes, and an unchanged input leaves its file untouched.
Before writing anything the build runs the checks below; if an input has a defect beyond `known_issues.json`, it stops and writes nothing.
The Rigveda clones live outside the repository, so without `--repos` the build re-renders the committed records and confirms the file is in canonical form.

`tests/pipeline/test_build.py` rebuilds the files in a scratch tree from scratch, builds again to show nothing changes, compares the bytes with the committed files, and checks that a duplicated ṛk in the input blocks every write.
The Data quality CI job runs `build --check`.

## Checks

Run every check with one command.

```bash
uv run python -m backend.pipeline.validate          # summary, exit 1 on a new defect
uv run python -m backend.pipeline.validate --show   # every issue with file, line and meter
```

| Check | Rules |
|---|---|
| Meter tables | header; gana string uses only य र त न भ ज स म ल ग and `-`; raw pattern uses only ल and ग, or l and g; syllable count, gana expansion and matra count agree with the pattern; pada number 1 to 5 |
| Rigveda | header; mandala 1 to 10 with positive sukta and rik; no repeated rk; text and meter present; pattern in ल and ग with a matching syllable count |
| Lineage | the data copy equals the source file; the Pragatha and Pankti file equals the matching Rigveda rows |
| Gita and examples | no empty or repeated verse; every meter in `examples.json` has an example |
| Registry | every dataset file exists in `backend/source/` and has the columns the registry names |

`backend/pipeline/known_issues.json` records how many issues each file carries today, per rule.
The command fails when a count goes above its recorded value, so a new defect cannot land unnoticed.
When a fix lowers a count, the command says so, and the baseline should be lowered in the same commit.

The Data quality job in `.github/workflows/ci.yml` runs the command, then `build --check`, then the corpus accuracy tests.

`tests/pipeline/test_data_quality.py` turns the same concerns into tests that run with the rest of the backend suite.

| Test | What it holds |
|---|---|
| Schema and size | each meter table, the Rigveda source, its copy, the Pragātha file, the Gita and the classical benchmark have their header and an exact row count |
| Duplicates | no ṛk twice in the Rigveda, no Gita verse twice; the classical benchmark repeats only its one known verse (rows 4 and 67) |
| Gana alphabet | `xfail(strict=True)` until the 1,204 rows below are fixed, so the defect stays visible; a second test fails as soon as that count grows |
| Blank rows | the only unnamed meter rows are empty spacer lines, 1 in sama and 15 in vishama |

## Known defects in the meter tables

These are recorded in `known_issues.json` and left as they are, because fixing them changes which meters the engine reports.

| Defect | Rows | Effect |
|---|---|---|
| Gana column outside the alphabet, 1,204 rows | 886 sama and 154 ardhasama in Latin l and g, 164 vishama holding pada labels such as `1दप` | the engine loads these imported rows but can never match them; most duplicate a Devanagari row that does match |
| Raw pattern disagrees with the gana or the counts | 16 gana mismatches, 165 syllable counts (5 sama, 160 imported vishama) and 27 matra counts | the pattern shown to users is wrong for those meters; matching uses the gana and is unaffected |
| Non-ल-ग characters in a raw pattern | 1 vedic, 154 ardhasama, 4 vishama | the Jagati row's pattern contains a Katakana character, and the imported ardhasama rows join two padas with `|` |

## Accuracy benchmarks

`backend/pipeline/benchmarks.py` loads two labelled sets and scores the engine on them.

| Benchmark | Size | Floors in `tests/test_corpus_accuracy.py` |
|---|---|---|
| Classical, first 147 rows of `page 1-47 chanda list - complete.csv` | 147 verses, 499 lines | 146 first lines, 134 whole verses line by line, 485 lines, 139 holistic verse results |
| Rigveda, `rigveda_with_meters_complete.csv` without verse-range labels | 9,247 rks | 8,067 exact meters, 9,009 exact or same family |

```bash
uv run pytest -m corpus                                   # the floors
uv run python -m backend.evaluation.csv_accuracy --all -v  # the classical report with every miss
uv run python -m backend.evaluation.rigveda_validation -v  # the Rigveda report per meter
```

`backend/tests/test_engine_golden.py` pins the full engine output on 150 verses drawn from these corpora, so a refactor that changes any result fails even when accuracy does not move.

## The Rigveda ground truth

`evaluation/data/rigveda_authentic.py` is generated; do not edit it by hand.
Clone the Rigveda_api and WSC2023 repositories side by side under one directory, then run the build.

```bash
uv run python -m backend.pipeline.rigveda_dataset --repos path/to/repos --check   # compare only
uv run python -m backend.pipeline.rigveda_dataset --repos path/to/repos           # write
```

The build validates every record and writes nothing if one fails.
Two builds from the same inputs write the same bytes, and `--check` exits 1 when the committed file differs.
`tests/pipeline/test_rigveda_dataset.py` runs the whole build on small fixture copies of both sources in `backend/tests/fixtures/rigveda_repos/`.
