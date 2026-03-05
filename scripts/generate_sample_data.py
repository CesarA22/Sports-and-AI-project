"""
Gera parquets de exemplo em data/processed/ para desenvolvimento.
Execute: python scripts/generate_sample_data.py
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

DATA_DIR = PROJECT_ROOT / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
N = 200

players = [f"Jogador_{i}" for i in range(1, N + 1)]
teams = ["Flamengo", "Palmeiras", "Corinthians", "São Paulo", "Santos", "Fluminense", "Botafogo", "Vasco", "Athletico", "Internacional"] * (N // 10 + 1)
positions = ["GK", "CB", "FB", "DM", "CM_AM", "W", "ST"]
position_groups = np.random.choice(positions, N)

master = pd.DataFrame({
    "player_key": [f"pk_{i}" for i in range(1, N + 1)],
    "player": players,
    "team": teams[:N],
    "season": np.random.choice([2023, 2024], N),
    "position_group": position_groups,
    "age": np.random.randint(18, 24, N),
    "minutes": np.random.randint(400, 2500, N),
})

feat_cols = ["xg_per90", "xa_per90", "prog_passes_per90", "prog_carries_per90", "tackles_per90", "pass_accuracy"]
features = master[["player_key", "season"]].copy()
for c in feat_cols:
    features[c] = np.random.randn(N) * 0.5 + np.random.rand(N)

umap_clusters = master[["player_key", "season"]].copy()
umap_clusters["umap_x"] = np.random.randn(N) * 2
umap_clusters["umap_y"] = np.random.randn(N) * 2
umap_clusters["cluster_id"] = np.random.randint(0, 5, N)
umap_clusters["cluster_prob"] = np.random.rand(N)
umap_clusters["is_noise"] = (np.random.rand(N) > 0.9).astype(int)

outliers = master[["player_key", "season"]].copy()
outliers["rarity_score"] = np.random.rand(N) * 0.5
outliers["impact_score"] = np.random.rand(N) * 0.5
outliers["prospect_score"] = outliers["rarity_score"] + outliers["impact_score"] + np.random.rand(N) * 0.3

master.to_parquet(DATA_DIR / "master.parquet", index=False)
features.to_parquet(DATA_DIR / "features.parquet", index=False)
umap_clusters.to_parquet(DATA_DIR / "umap_clusters.parquet", index=False)
outliers.to_parquet(DATA_DIR / "outliers.parquet", index=False)

# Player cards (JSONL)
with open(DATA_DIR / "player_cards.jsonl", "w", encoding="utf-8") as f:
    for _, row in master.iterrows():
        card = {
            "player_key": row["player_key"],
            "player": row["player"],
            "team": row["team"],
            "season": int(row["season"]),
            "card": f"{row['player']} ({row['team']}, {row['season']}) - {row['position_group']}, {row['minutes']} min.",
        }
        f.write(json.dumps(card, ensure_ascii=False) + "\n")

print(f"Sample data written to {DATA_DIR}")
