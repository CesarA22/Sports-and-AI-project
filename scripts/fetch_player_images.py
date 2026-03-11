"""
Gera player_images.parquet via Wikidata → Commons.
Execute: python scripts/fetch_player_images.py
Requer: pip install requests pyarrow
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from config import MASTER_PARQUET, PLAYER_IMAGES_PARQUET
from src.data.player_images import fetch_all_player_images

if __name__ == "__main__":
    if not MASTER_PARQUET.exists():
        print("master.parquet não encontrado. Rode generate_sample_data.py primeiro.")
        sys.exit(1)
    master = pd.read_parquet(MASTER_PARQUET)
    print(f"Processando {len(master)} jogadores...")
    df = fetch_all_player_images(master)
    df.to_parquet(PLAYER_IMAGES_PARQUET, index=False)
    with_url = df["image_url"].notna().sum()
    print(f"player_images.parquet salvo. {with_url}/{len(df)} com foto.")
