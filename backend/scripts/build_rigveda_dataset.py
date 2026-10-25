#!/usr/bin/env python3
"""Build backend/evaluation/data/rigveda_authentic.py from Rigveda_api and WSC2023.

The generated file names this command, so it stays as an entry point; the build
itself lives in backend/pipeline/rigveda_dataset.py. Pass --repos DIR when the
two clones are not under repos/ at the repository root, and --check to compare
without writing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.pipeline.rigveda_dataset import main

if __name__ == '__main__':
    sys.exit(main())
