"""Base components: avatar, get_image_url."""
from typing import Optional
import pandas as pd


def get_image_url(player_key: str, images_df: pd.DataFrame) -> Optional[str]:
    if images_df.empty or "player_key" not in images_df.columns:
        return None
    match = images_df[images_df["player_key"].astype(str) == str(player_key)]
    if match.empty:
        return None
    url = match.iloc[0].get("image_url")
    return url if pd.notna(url) and url else None


def render_player_avatar(
    player_key: str, player_name: str, images_df: pd.DataFrame, size: int = 48
) -> str:
    url = get_image_url(player_key, images_df)
    if url:
        return f'<img src="{url}" width="{size}" height="{size}" style="border-radius:50%;object-fit:cover" alt="{player_name}"/>'
    initials = "".join(w[0] for w in str(player_name).split()[:2]).upper()[:2] if player_name else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#444;color:#fff;display:flex;align-items:center;justify-content:center;font-size:{size//3}px;font-weight:bold">{initials}</div>'
