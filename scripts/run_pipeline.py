"""
Executa o pipeline de ingestão (dados reais do FBref).
  python scripts/run_pipeline.py
  python scripts/run_pipeline.py --seasons 2023 2024
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=int, nargs="+", default=[2023, 2024])
    args = parser.parse_args()

    from src.pipeline.ingest import run_pipeline

    ok = run_pipeline(seasons=args.seasons)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
