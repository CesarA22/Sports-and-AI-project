"""
Answer Writer - LLM redige resposta usando apenas evidence, com instruções rígidas.
"""
import json
import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)


def _build_writer_prompt(question: str, plan: dict, evidence: Any, ai_insight: str = "") -> str:
    ai_block = ""
    if ai_insight and len(ai_insight) > 20:
        ai_block = f"\nCONTEXTO (insight de IA recente - usuário pode referenciar):\n{ai_insight[:600]}\n"
    return f"""Você é um assistente de scout de futebol. Responda APENAS com base nas evidências fornecidas.{ai_block}

PERGUNTA DO USUÁRIO:
{question}

PLANO VALIDADO:
{json.dumps(plan, ensure_ascii=False, default=str)}

EVIDÊNCIA (dados retornados pelas ferramentas):
{json.dumps(evidence, ensure_ascii=False, default=str)}

REGRAS OBRIGATÓRIAS:
1. Use SOMENTE as informações presentes na evidência. Não invente dados.
2. Se a evidência contiver "error" (ex: "É necessário especificar 2 jogadores"), responda de forma amigável orientando o usuário. Ex: "Para comparar, indique os nomes: Compare Jogador 1 vs Jogador 2."
3. Se a evidência for vazia ou incompleta sem mensagem de erro, responda: "Não tenho dados no escopo do projeto para afirmar isso."
4. Inclua OBRIGATORIAMENTE no final um bloco "Fontes (dataset):" listando:
   - player_key ou player_id
   - season
   - team
   - colunas usadas
5. Não mencione temporadas fora de 2023 e 2024.
6. Não mencione métricas que não estão na evidência.
7. Seja conciso e direto."""


def run_writer(question: str, plan: dict, evidence: Any, ai_insight: str = "") -> str:
    """
    Chama o LLM para escrever a resposta final.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key não configurada. Configure OPENAI_API_KEY no .env"

    prompt = _build_writer_prompt(question, plan, evidence, ai_insight)

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.exception("Writer error: %s", e)
        return f"Erro ao gerar resposta: {e}"
