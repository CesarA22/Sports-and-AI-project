# Scout Radar

App Streamlit com **Visualizer** (UMAP, clusters, outliers, comparação) e **Chatbot grounded** com guardrails para análise de jogadores do Campeonato Brasileiro Série A (2023/2024).

## Features

- **Metric Registry** - tooltips em tabelas e gráficos explicando cada métrica
- **Fotos dos jogadores** - via Wikidata (P18) → Wikimedia Commons, com cache e fallback silhueta
- **Identidade correta** - `player` real em master/umap/outliers (sem jogador_i)
- **UI moderna** - tema dark, cards, Auditoria legível

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env: OPENAI_API_KEY e opcionalmente DATA_MODE, DATA_BUNDLE_URL
```

### DATA_MODE

- **local** (default): usa `data/processed/` existente. Rode `python scripts/generate_sample_data.py` antes.
- **download**: baixa bundle do `DATA_BUNDLE_URL` na primeira execução.
- **build**: roda pipeline automaticamente (gera sample data).

## Dados

Coloque os parquets em `data/processed/`:

- `master.parquet` - identidade (player, team, season, position_group, minutes, age)
- `features.parquet` - métricas per90, z-scores
- `umap_clusters.parquet` - player, team, season, umap_x/y, cluster_id
- `outliers.parquet` - player, team, season, prospect_score
- `player_cards.jsonl` - cards textuais (opcional)
- `player_images.parquet` - fotos (opcional, gerado por script)

**Pipeline (dados reais do FBref):**
```bash
pip install soccerdata
python scripts/run_pipeline.py --seasons 2023 2024
```

**Dados de exemplo (fallback):**
```bash
python scripts/generate_sample_data.py
```

Para buscar fotos via Wikidata/Commons (requer internet):

```bash
python scripts/fetch_player_images.py
```

## Executar

```bash
streamlit run app.py
```

## Testes de segurança

```bash
python -m pytest tests/test_prompt_injection.py -v
```

## Publicar dados (GitHub Release / bucket)

```bash
python scripts/generate_sample_data.py
python scripts/create_bundle.py
# Upload data/processed_bundle.zip como Release asset ou em bucket
```

Configure `DATA_BUNDLE_URL` com a URL direta do zip (ex: GitHub Release asset).

### Buckets gratuitos

| Opção | Free tier | Notas |
|-------|-----------|-------|
| **GitHub Releases** | 2GB/asset | Simples, ideal para portfólio |
| **Cloudflare R2** | 10GB/mês | Zero egress, precisa conta |
| **Hugging Face** | Ilimitado (datasets públicos) | Versionado, viralização |
| **Backblaze B2** | 10GB | Parceria com Cloudflare (egress free) |
| **Google Cloud Storage** | 5GB/mês | 12 meses free |

Para começar: **GitHub Releases** (sem conta extra).

## Arquitetura do Chatbot

1. **Policy Gate** (determinístico) - bloqueia prompt injection e fora do escopo
2. **Router/Planner** (LLM + Structured Outputs) - decide intent, filtros, entidades
3. **Tools** (DuckDB/pandas) - executa queries no dataset local
4. **Answer Writer** (LLM) - redige resposta com evidências
5. **Post-check** - garante "Fontes (dataset)" e métricas no escopo
