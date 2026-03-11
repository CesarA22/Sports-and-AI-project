"""
Router / Planner - LLM com Structured Outputs para decidir o plano de consulta.
"""
import json
import logging
import os
import re
from typing import Any

from openai import OpenAI

from config import (
    METRICS_ALLOWLIST,
    POSITION_GROUPS,
    SEASONS_ALLOWED,
    K_MAX,
)

logger = logging.getLogger(__name__)

# JSON Schema para o planner - TODOS os objetos precisam de additionalProperties: false
PLANNER_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "player_profile",
                "compare",
                "top_k",
                "similar",
                "cluster_explain",
                "methodology",
                "out_of_scope",
            ],
        },
        "filters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "season": {"type": "array", "items": {"type": "integer"}},
                "position_group": {"type": "array", "items": {"type": "string"}},
                "team": {"type": "array", "items": {"type": "string"}},
                "age_max": {"type": "integer"},
                "minutes_min": {"type": "integer"},
            },
            "required": ["season", "position_group", "team", "age_max", "minutes_min"],
        },
        "entities": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "players": {"type": "array", "items": {"type": "string"}},
                "cluster_id": {"type": "integer"},
            },
            "required": ["players", "cluster_id"],
        },
        "metrics": {"type": "array", "items": {"type": "string"}},
        "k": {"type": "integer"},
        "reason": {"type": "string"},
    },
    "required": ["intent", "filters", "entities", "metrics", "k", "reason"],
}


def _build_planner_prompt(
    user_message: str,
    context: dict[str, Any],
) -> str:
    season = context.get("season", 2024)
    position_group = context.get("position_group", "CM_AM")
    minutes_min = context.get("minutes_min", 600)
    age_max = context.get("age_max", 23)

    metrics_list = sorted(METRICS_ALLOWLIST - {"minutes", "age", "position_group", "team", "season"})
    metrics_str = ", ".join(metrics_list[:20])

    ai_insight = context.get("ai_insight", "") or ""
    ai_ctx_block = ""
    if ai_insight and len(ai_insight) > 20:
        ai_ctx_block = f"\n\nCONTEXT (recent AI insight - user may refer to this):\n{ai_insight[:800]}\n"

    return f"""You are a query planner for a football analytics application.

Your job is ONLY to classify the user question and extract parameters.{ai_ctx_block}

Valid intents:
- player_profile: perfil de um jogador específico
- compare: comparar dois jogadores (use mesmo se o usuário não nomear os jogadores; entities.players pode ficar vazio)
- top_k: ranking top N por métrica (ex: "top 10 por prospect_score" -> intent=top_k, metrics=[prospect_score], k=10)
- similar: jogadores similares a X
- cluster_explain: explicar um cluster
- methodology: perguntas sobre como o modelo/clustering/UMAP/outliers/prospect_score foram calculados
- out_of_scope: notícias, transferências, outras ligas, pedidos de internet/system prompt

IMPORTANTE: methodology = perguntas sobre "como funciona", "explique o método", "metodologia do projeto".
NUNCA classifique essas como out_of_scope.

CONTEXTO:
- season: {season}
- position_group: {position_group}
- minutes_min: {minutes_min}
- age_max: {age_max}

Métricas disponíveis: {metrics_str}

PERGUNTA:
{user_message}

EXEMPLOS IMPORTANTES:
- "compare jogador 27 com jogador 24" -> intent=compare, entities.players=["Jogador 27","Jogador 24"]
- "analise o jogador 24 com o 50" -> intent=compare, entities.players=["Jogador 24","Jogador 50"]
- "analisando players de 2024, analise jogador 10 com 20" -> intent=compare, entities.players=["Jogador 10","Jogador 20"]
- "jogador 5 vs jogador 10" -> intent=compare, entities.players=["Jogador 5","Jogador 10"]
- "analisar" e "analise" = compare. Números "jogador N" ou "com o N" -> "Jogador N".

Return only JSON matching the schema. Prefira SEMPRE uma intent válida (compare, top_k, etc.) em vez de out_of_scope."""


# Mapeamento de variações de intent (PT/EN, maiúsculas, etc.)
INTENT_ALIASES = {
    "comparar": "compare",
    "comparação": "compare",
    "comparison": "compare",
    "analise": "compare",
    "analisar": "compare",
    "analyze": "compare",
    "top": "top_k",
    "ranking": "top_k",
    "rank": "top_k",
    "similar": "similar",
    "similares": "similar",
    "metodologia": "methodology",
    "methodology": "methodology",
    "cluster": "cluster_explain",
    "perfil": "player_profile",
    "profile": "player_profile",
}


def _normalize_intent(raw: Any) -> str | None:
    """Normaliza intent para um valor válido do enum."""
    if raw is None or raw == "NULL" or str(raw).lower() == "null":
        return None
    s = str(raw).strip().lower()
    if s in INTENT_ALIASES:
        return INTENT_ALIASES[s]
    # Verificar enum direto
    valid = set(PLANNER_JSON_SCHEMA["properties"]["intent"]["enum"])
    if s in valid:
        return s
    # Tentar match parcial (ex: "compare_players" -> "compare")
    for v in valid:
        if v in s or s in v:
            return v
    return None


def _heuristic_compare_plan(user_message: str) -> dict | None:
    """
    Extrai intent=compare e players de mensagens como:
    - "compare jogador 27 com jogador 24"
    - "analise o jogador 24 com o 50"
    - "jogador 5 vs jogador 10"
    Retorna None se não conseguir inferir.
    """
    msg = (user_message or "").lower()
    # Inclui "analise/analisar" (analisar = comparar neste contexto)
    if not re.search(r"compar(e|ar)|analis(e|ar)|vs\.?|versus", msg):
        return None

    # Coletar números de jogadores (evitar anos 2020-2029)
    nums = []
    # Padrão 1: "jogador N", "player N"
    nums.extend(re.findall(r"(?:jogador|player)s?\s*(\d+)", msg, re.IGNORECASE))
    # Padrão 2: "com o N", "com N", "e o N" (ex: "jogador 24 com o 50")
    nums.extend(re.findall(r"(?:com\s+o|com|e\s+o)\s+(\d+)\b", msg, re.IGNORECASE))
    # Padrão 3: "jogador N e N" - segundo número isolado
    nums.extend(re.findall(r"jogador\s+\d+\s+e\s+(\d+)\b", msg, re.IGNORECASE))
    # Filtrar anos (2023, 2024, etc.)
    nums = [n for n in nums if not (len(n) == 4 and n.startswith("20"))]
    # Manter ordem e remover duplicatas preservando ordem
    seen = set()
    unique = []
    for n in nums:
        if n not in seen:
            seen.add(n)
            unique.append(n)

    if len(unique) >= 2:
        players = [f"Jogador {n}" for n in unique[:2]]
        return {
            "intent": "compare",
            "filters": {"season": [2024], "position_group": ["CM_AM"], "age_max": 23, "minutes_min": 600, "team": []},
            "entities": {"players": players, "cluster_id": None},
            "metrics": [],
            "k": 10,
            "reason": "Comparação inferida pela mensagem.",
        }

    # Fallback: nomes explícitos "Jogador X" no texto
    pat2 = re.compile(r"Jogador\s+\d+", re.IGNORECASE)
    names = pat2.findall(user_message or "")
    if len(names) >= 2:
        players = []
        for n in names[:2]:
            m = re.search(r"\d+", n)
            if m:
                players.append(f"Jogador {m.group()}")
        if len(players) >= 2:
            return {
                "intent": "compare",
                "filters": {"season": [2024], "position_group": ["CM_AM"], "age_max": 23, "minutes_min": 600, "team": []},
                "entities": {"players": players, "cluster_id": None},
                "metrics": [],
                "k": 10,
                "reason": "Comparação inferida pela mensagem.",
            }
    return None


def _validate_and_fix_plan(plan: dict, user_message: str = "") -> dict:
    """Valida e corrige o plano retornado pelo LLM."""
    valid_intents = set(PLANNER_JSON_SCHEMA["properties"]["intent"]["enum"])
    default_plan = {
        "intent": "out_of_scope",
        "filters": {"season": [2024], "position_group": ["CM_AM"], "age_max": 23, "minutes_min": 600, "team": []},
        "entities": {"players": [], "cluster_id": None},
        "metrics": [],
        "k": 10,
        "reason": "Resposta inválida do planner.",
    }

    if plan is None or not isinstance(plan, dict):
        # Tentar heuristic antes de desistir
        heuristic = _heuristic_compare_plan(user_message)
        return heuristic if heuristic else default_plan

    intent = plan.get("intent")
    normalized = _normalize_intent(intent)
    if normalized:
        plan["intent"] = normalized
    elif intent is None or intent == "NULL" or str(intent).lower() == "null" or intent not in valid_intents:
        # Intent inválido: tentar heuristic de compare
        heuristic = _heuristic_compare_plan(user_message)
        if heuristic:
            plan.update(heuristic)
        else:
            plan["intent"] = "out_of_scope"
            plan["reason"] = plan.get("reason") or "Intent não reconhecida. Por favor, reformule a pergunta."

    filters = plan.get("filters") or {}
    entities = plan.get("entities") or {}
    if not isinstance(filters, dict):
        filters = {}
    if not isinstance(entities, dict):
        entities = {}

    plan["filters"] = dict(filters)
    plan["entities"] = {"players": entities.get("players") or [], "cluster_id": entities.get("cluster_id")}

    # seasons válidos
    seasons = filters.get("season") or [2024]
    if not isinstance(seasons, list):
        seasons = [seasons] if seasons is not None else [2024]
    plan["filters"]["season"] = [s for s in seasons if s in SEASONS_ALLOWED]
    if not plan["filters"]["season"]:
        plan["filters"]["season"] = [2024]

    # position_group válidos
    pg = filters.get("position_group") or ["CM_AM"]
    if not isinstance(pg, list):
        pg = [pg] if pg else ["CM_AM"]
    plan["filters"]["position_group"] = [p for p in pg if p in POSITION_GROUPS]
    if not plan["filters"]["position_group"]:
        plan["filters"]["position_group"] = ["CM_AM"]

    # Garantir age_max e minutes_min em filters
    if "age_max" not in plan["filters"] or plan["filters"]["age_max"] is None:
        plan["filters"]["age_max"] = 23
    if "minutes_min" not in plan["filters"] or plan["filters"]["minutes_min"] is None:
        plan["filters"]["minutes_min"] = 600
    if "team" not in plan["filters"]:
        plan["filters"]["team"] = []

    # metrics dentro da allowlist
    metrics = plan.get("metrics") or []
    plan["metrics"] = [m for m in metrics if m in METRICS_ALLOWLIST]

    # k limitado
    k = plan.get("k") or 10
    plan["k"] = min(max(1, int(k)), K_MAX)

    return plan


def run_planner(user_message: str, context: dict[str, Any]) -> dict:
    """
    Chama o LLM para obter o plano estruturado.
    Valida e retorna o plano pronto para as tools.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "intent": "out_of_scope",
            "filters": {"season": [2024], "position_group": ["CM_AM"], "age_max": 23, "minutes_min": 600},
            "entities": {"players": [], "cluster_id": None},
            "metrics": [],
            "k": 10,
            "reason": "OpenAI API key não configurada.",
        }

    prompt = _build_planner_prompt(user_message, context)

    try:
        client = OpenAI()
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "planner_output",
                "strict": False,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "intent": {"type": "string", "enum": list(PLANNER_JSON_SCHEMA["properties"]["intent"]["enum"])},
                        "filters": PLANNER_JSON_SCHEMA["properties"]["filters"],
                        "entities": PLANNER_JSON_SCHEMA["properties"]["entities"],
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "k": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["intent", "filters", "entities", "metrics", "k", "reason"],
                },
            },
        }
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format=response_format,
            )
            parsed = response.choices[0].message.parsed
            plan = dict(parsed) if hasattr(parsed, "model_dump") else (parsed if isinstance(parsed, dict) else {})
        except (AttributeError, TypeError):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format=response_format,
            )
            content = response.choices[0].message.content
            plan = json.loads(content) if content else {}
        if plan is None:
            plan = {}
    except Exception as e:
        logger.exception("Planner error: %s", e)
        plan = None  # Permite heuristic fallback em _validate_and_fix_plan

    return _validate_and_fix_plan(plan, user_message)
