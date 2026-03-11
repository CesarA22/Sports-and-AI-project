"""
Player images via Wikidata (P18) → Wikimedia Commons.
Resolve player name to QID, fetch image URL, cache localmente.
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import pandas as pd
import requests

from config import CACHE_DIR, PLAYER_IMAGES_PARQUET

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
THUMB_SIZE = 256
REQUEST_DELAY = 0.3  # evita rate limit


def _load_cache() -> dict:
    cache_path = CACHE_DIR / "player_images.json"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict):
    cache_path = CACHE_DIR / "player_images.json"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _search_wikidata(query: str, country: str = "Brazil") -> Optional[str]:
    """Busca item no Wikidata: futebolista brasileiro."""
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "pt",
        "format": "json",
        "type": "item",
    }
    try:
        r = requests.get(WIKIDATA_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("search", [])
        if not results:
            return None
        for item in results[:5]:
            qid = item.get("id")
            if not qid:
                continue
            # Verificar se é futebolista
            desc = (item.get("description") or "").lower()
            if "futebolista" in desc or "futebol" in desc or "football" in desc:
                return qid
        return results[0]["id"] if results else None
    except Exception as e:
        logger.warning("Wikidata search failed for %s: %s", query, e)
        return None


def _get_p18(qid: str) -> Optional[str]:
    """Obtém P18 (image) do item Wikidata."""
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims",
        "format": "json",
    }
    try:
        r = requests.get(WIKIDATA_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        entities = data.get("entities", {})
        ent = entities.get(qid)
        if not ent:
            return None
        claims = ent.get("claims", {})
        p18 = claims.get("P18", [])
        if not p18:
            return None
        filename = p18[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
        return filename
    except Exception as e:
        logger.warning("Wikidata P18 fetch failed for %s: %s", qid, e)
        return None


def _get_thumb_url(filename: str) -> Optional[str]:
    """Obtém URL da thumbnail via Commons API."""
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": THUMB_SIZE,
        "format": "json",
    }
    try:
        r = requests.get(COMMONS_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            infos = p.get("imageinfo", [])
            if infos:
                return infos[0].get("thumburl") or infos[0].get("url")
        return None
    except Exception as e:
        logger.warning("Commons imageinfo failed for %s: %s", filename, e)
        return None


def resolve_player_image(player: str, player_key: str, team: Optional[str] = None) -> dict:
    """
    Resolve imagem do jogador. Retorna {player_key, player, wikidata_qid?, image_url?, license?}.
    Usa cache por player_key.
    """
    cache = _load_cache()
    if player_key in cache:
        return {"player_key": player_key, "player": player, **cache[player_key]}

    out = {"player_key": player_key, "player": player, "wikidata_qid": None, "image_url": None, "license": "CC"}
    qid = _search_wikidata(player)
    time.sleep(REQUEST_DELAY)
    if not qid:
        _save_cache({**cache, player_key: out})
        return out
    out["wikidata_qid"] = qid
    filename = _get_p18(qid)
    time.sleep(REQUEST_DELAY)
    if not filename:
        _save_cache({**cache, player_key: out})
        return out
    url = _get_thumb_url(filename)
    if url:
        out["image_url"] = url
    _save_cache({**cache, player_key: out})
    return out


def fetch_all_player_images(master_df: pd.DataFrame) -> pd.DataFrame:
    """Processa todos os jogadores do master e gera player_images.parquet."""
    rows = []
    for _, row in master_df.iterrows():
        pk = row.get("player_key", row.get("player", ""))
        player = row.get("player", str(pk))
        team = row.get("team")
        r = resolve_player_image(player, str(pk), team)
        rows.append(r)
    return pd.DataFrame(rows)


def load_player_images() -> pd.DataFrame:
    """Carrega player_images.parquet."""
    if not PLAYER_IMAGES_PARQUET.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(PLAYER_IMAGES_PARQUET)
    except Exception as e:
        logger.warning("Failed to load player_images: %s", e)
        return pd.DataFrame()


def get_image_url(player_key: str, images_df: pd.DataFrame) -> Optional[str]:
    """Retorna URL da imagem ou None (usa fallback silhueta)."""
    if images_df.empty:
        return None
    match = images_df[images_df["player_key"].astype(str) == str(player_key)]
    if match.empty:
        return None
    url = match.iloc[0].get("image_url")
    return url if pd.notna(url) and url else None
