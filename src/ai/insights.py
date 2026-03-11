"""
AI-generated insights: clusters and player comparison.
"""
import os
from typing import Optional

from openai import OpenAI


def _client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _lang_instruction(locale: str) -> str:
    if locale == "pt":
        return "Responda APENAS em português brasileiro."
    if locale == "es":
        return "Responde ÚNICAMENTE en español."
    return "Respond ONLY in English."


def generate_explorer_insights(
    top_prospects: str,
    by_team: str,
    by_position: str,
    filter_desc: str,
    locale: str = "pt",
) -> str:
    """Gera insights sobre jogadores, times e prospectos conforme filtros atuais."""
    client = _client()
    if not client:
        return "*OpenAI API key não configurada. Configure OPENAI_API_KEY no .env*"

    lang = _lang_instruction(locale)
    prompt = f"""Você é um scout de futebol. Analise os dados e dê insights ESPECÍFICOS sobre:
- Melhores prospectos (nomes, times, scores)
- Times com mais destaque
- Padrões por posição
- Recomendações de scouting

Filtros atuais: {filter_desc}

TOP PROSPECTOS (nome, time, prospect_score): {top_prospects}
POR TIME: {by_team}
POR POSIÇÃO: {by_position}

Seja objetivo. Máx 6 bullets. Use NOMES de jogadores e times. {lang}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        text = r.choices[0].message.content or ""
        return text.strip()
    except Exception as e:
        return f"*Erro ao gerar insights: {e}*"


def generate_player_insight(player_name: str, metrics_text: str, locale: str = "pt") -> str:
    """Gera insight de scouting para um único jogador."""
    client = _client()
    if not client:
        return "*OpenAI API key não configurada. Configure OPENAI_API_KEY no .env*"

    lang = _lang_instruction(locale)
    prompt = f"""Scouting insight for U23 player. OBJECTIVE, max 4 bullets, 1 sentence each. {lang}
PLAYER: {player_name}
METRICS: {metrics_text}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = r.choices[0].message.content or ""
        return text.strip()
    except Exception as e:
        return f"*Erro ao gerar relatório: {e}*"


def generate_comparison_insights(
    player_a: str,
    player_b: str,
    metrics_text: str,
    locale: str = "pt",
) -> str:
    """Gera insights comparando dois jogadores."""
    client = _client()
    if not client:
        return "*OpenAI API key não configurada. Configure OPENAI_API_KEY no .env*"

    lang = _lang_instruction(locale)
    prompt = f"""Compare two U23 players. OBJECTIVE, max 4 bullets. Use numbers. {lang}
A: {player_a} | B: {player_b}
METRICS: {metrics_text}
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        text = r.choices[0].message.content or ""
        return text.strip()
    except Exception as e:
        return f"*Erro ao gerar insights: {e}*"
