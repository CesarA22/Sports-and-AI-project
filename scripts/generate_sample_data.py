"""
Gera parquets de exemplo em data/processed/ para desenvolvimento.
Formato simples: Jogador 1, Jogador 2... (dados sintéticos, sem nomes reais).
Execute: python scripts/generate_sample_data.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

DATA_DIR = PROJECT_ROOT / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

N = 200
np.random.seed(42)

# Nomes simples: Jogador 1, Jogador 2, ...
players_used = [f"Jogador {i+1}" for i in range(N)]
seasons = np.random.choice([2023, 2024], N)
teams_list = ["Time A", "Time B", "Time C", "Time D", "Time E", "Time F", "Time G", "Time H", "Time I", "Time J"]
teams = (teams_list * (N // len(teams_list) + 1))[:N]
positions = list(np.random.choice(["GK", "CB", "FB", "DM", "CM_AM", "W", "ST"], N))


def _make_key(name: str, season: int) -> str:
    slug = name.lower().replace(" ", "_").replace(".", "")
    return f"{slug}_{season}"


master = pd.DataFrame({
    "player_key": [_make_key(p, int(s)) for p, s in zip(players_used, seasons)],
    "player": players_used,
    "team": teams,
    "season": seasons,
    "position_group": positions,
    "age": np.random.randint(18, 24, N),
    "minutes": np.random.randint(400, 2500, N),
})

master = master.drop_duplicates(subset=["player_key", "season"], keep="first").reset_index(drop=True)

feat_cols = ["xg_per90", "xa_per90", "prog_passes_per90", "prog_carries_per90", "tackles_per90", "pass_accuracy"]
features = master[["player_key", "season"]].copy()
for c in feat_cols:
    features[c] = np.random.randn(len(master)) * 0.5 + np.random.rand(len(master))

umap_clusters = master[["player_key", "player", "team", "season", "position_group"]].copy()
umap_clusters["umap_x"] = np.random.randn(len(master)) * 2
umap_clusters["umap_y"] = np.random.randn(len(master)) * 2
umap_clusters["cluster_id"] = np.random.randint(0, 5, len(master))
umap_clusters["cluster_prob"] = np.random.rand(len(master))
umap_clusters["is_noise"] = (np.random.rand(len(master)) > 0.9).astype(int)

outliers = master[["player_key", "player", "team", "season"]].copy()
outliers["rarity_score"] = np.random.rand(len(master)) * 0.5
outliers["impact_score"] = np.random.rand(len(master)) * 0.5
outliers["prospect_score"] = outliers["rarity_score"] + outliers["impact_score"] + np.random.rand(len(master)) * 0.3

master.to_parquet(DATA_DIR / "master.parquet", index=False)
features.to_parquet(DATA_DIR / "features.parquet", index=False)
umap_clusters.to_parquet(DATA_DIR / "umap_clusters.parquet", index=False)
outliers.to_parquet(DATA_DIR / "outliers.parquet", index=False)

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

import hashlib
def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()

meta = {
    "source": "sample/generate_sample_data",
    "seasons": [2023, 2024],
    "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "schema_version": 1,
    "row_count": {"master": len(master)},
    "hashes": {},
}
for f in ["master.parquet", "features.parquet", "umap_clusters.parquet", "outliers.parquet"]:
    p = DATA_DIR / f
    if p.exists():
        meta["hashes"][f] = _sha(p)
with open(DATA_DIR / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"Sample data written to {DATA_DIR}")
print(f"  master: {len(master)} rows (Jogador 1..{N})")
print(f"  metadata.json created")
