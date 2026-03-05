"""
Answer Writer - LLM redige resposta usando apenas evidence, com instruções rígidas.
"""
import json
import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)


def _build_writer_prompt(question: str, plan: dict, evidence: Any) -> str:
    return f"""Você é um assistente de scout de futebol. Responda APENAS com base nas evidências fornecidas.

PERGUNTA DO USUÁRIO:
{question}

PLANO VALIDADO:
{json.dumps(plan, ensure_ascii=False, default=str)}

EVIDÊNCIA (dados retornados pelas ferramentas):
{json.dumps(evidence, ensure_ascii=False, default=str)}

REGRAS OBRIGATÓRIAS:
1. Use SOMENTE as informações presentes na evidência. Não invente dados.
2. Se a evidência for vazia, incompleta ou indicar erro, responda: "Não tenho dados no escopo do projeto para afirmar isso."
3. Inclua OBRIGATORIAMENTE no final um bloco "Fontes (dataset):" listando:
   - player_key ou player_id
   - season
   - team
   - colunas usadas
4. Não mencione temporadas fora de 2023 e 2024.
5. Não mencione métricas que não estão na evidência.
6. Seja conciso e direto."""


def run_writer(question: str, plan: dict, evidence: Any) -> str:
    """
    Chama o LLM para escrever a resposta final.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key não configurada. Configure OPENAI_API_KEY no .env"

    prompt = _build_writer_prompt(question, plan, evidence)

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
