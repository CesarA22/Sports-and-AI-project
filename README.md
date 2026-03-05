# Scout Radar

App Streamlit com **Visualizer** (UMAP, clusters, outliers, comparação) e **Chatbot grounded** com guardrails para análise de jogadores do Campeonato Brasileiro Série A (2023/2024).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

## Dados

Coloque os parquets em `data/processed/`:

- `master.parquet` - identidade, minutos, idade, posição, time
- `features.parquet` - métricas per90, z-scores
- `umap_clusters.parquet` - umap_x, umap_y, cluster_id
- `outliers.parquet` - rarity_score, impact_score, prospect_score
- `player_cards.jsonl` - cards textuais (opcional)

Para gerar dados de exemplo:

```bash
python scripts/generate_sample_data.py
```

## Executar

```bash
streamlit run app.py
```

## Testes de segurança

```bash
pytest tests/test_prompt_injection.py -v
```

## Arquitetura do Chatbot

1. **Policy Gate** (determinístico) - bloqueia prompt injection e fora do escopo
2. **Router/Planner** (LLM + Structured Outputs) - decide intent, filtros, entidades
3. **Tools** (DuckDB/pandas) - executa queries no dataset local
4. **Answer Writer** (LLM) - redige resposta com evidências
5. **Post-check** - garante "Fontes (dataset)" e métricas no escopo
