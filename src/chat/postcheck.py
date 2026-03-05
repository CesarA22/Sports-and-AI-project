"""
Pós-checagem - garante que a resposta obedece ao escopo.
"""
import re
from typing import Tuple

from config import METRICS_ALLOWLIST, SEASONS_ALLOWED


def check_response(text: str) -> Tuple[bool, str]:
    """
    Verifica se a resposta está em conformidade.
    Retorna (ok, mensagem_de_erro).
    """
    if not text or not isinstance(text, str):
        return False, "Resposta vazia."

    # 1. Presença de "Fontes (dataset)"
    if "Fontes (dataset)" not in text and "fontes" not in text.lower():
        return False, "Falta bloco 'Fontes (dataset)'."

    # 2. Temporadas fora de 2023/2024
    year_match = re.findall(r"\b(19\d{2}|20[0-1]\d|202[5-9])\b", text)
    for y in year_match:
        yr = int(y)
        if yr not in SEASONS_ALLOWED and 2015 <= yr <= 2030:
            return False, f"Menção a temporada fora do escopo: {yr}"

    # 3. Métricas fora da allowlist (heurística: palavras que parecem métricas)
    words = set(re.findall(r"\b[a-z_]+_per90\b|\b[a-z_]+_score\b", text.lower()))
    invalid = words - METRICS_ALLOWLIST
    if invalid:
        # Só falhar se for claramente uma métrica de futebol que não temos
        known_invalid = {"heatmap", "expected_goals_against", "penalties_saved"}
        if invalid & known_invalid:
            return False, f"Métricas fora do escopo: {invalid}"

    return True, ""
