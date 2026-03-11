"""
Metric Registry - fonte única da verdade para labels, descrições e tooltips.
Usado em tabelas (column_config), gráficos (hovertemplate) e comparador.
"""
from typing import Optional

METRIC_INFO: dict[str, dict] = {
    "xg_per90": {
        "label": "xG/90",
        "desc": "Expected Goals por 90 minutos: qualidade/quantidade das chances finalizadas.",
        "unit": "gols esperados/90",
        "higher_is_better": True,
        "group": "Finalização",
    },
    "xa_per90": {
        "label": "xA/90",
        "desc": "Expected Assists por 90 minutos: qualidade das passes que levam a finalização.",
        "unit": "assistências esperadas/90",
        "higher_is_better": True,
        "group": "Criação",
    },
    "prog_passes_per90": {
        "label": "Passes Prog./90",
        "desc": "Passes progressivos: passes que avançam a bola significativamente em direção ao gol.",
        "unit": "passes/90",
        "higher_is_better": True,
        "group": "Criação",
    },
    "prog_carries_per90": {
        "label": "Conduções Prog./90",
        "desc": "Conduções progressivas: progressão da bola com os pés em direção ao gol.",
        "unit": "conduções/90",
        "higher_is_better": True,
        "group": "Progressão",
    },
    "touches_box_per90": {
        "label": "Toques na Área/90",
        "desc": "Toques na área adversária: participação ofensiva próxima ao gol.",
        "unit": "toques/90",
        "higher_is_better": True,
        "group": "Finalização",
    },
    "tackles_per90": {
        "label": "Desarmes/90",
        "desc": "Desarmes bem-sucedidos por 90 minutos.",
        "unit": "desarmes/90",
        "higher_is_better": True,
        "group": "Defesa",
    },
    "interceptions_per90": {
        "label": "Interceptações/90",
        "desc": "Interceptações de passes adversários.",
        "unit": "interceptações/90",
        "higher_is_better": True,
        "group": "Defesa",
    },
    "aerial_won_per90": {
        "label": "Duelos Aéreos/90",
        "desc": "Duelos aéreos ganhos por 90 minutos.",
        "unit": "duelos/90",
        "higher_is_better": True,
        "group": "Defesa",
    },
    "passes_completed_per90": {
        "label": "Passes Completos/90",
        "desc": "Passes completados com sucesso por 90 minutos.",
        "unit": "passes/90",
        "higher_is_better": True,
        "group": "Passe",
    },
    "pass_accuracy": {
        "label": "% Passes",
        "desc": "Percentual de passes completados.",
        "unit": "%",
        "higher_is_better": True,
        "group": "Passe",
    },
    "pressures_per90": {
        "label": "Pressões/90",
        "desc": "Pressões aplicadas na equipe adversária.",
        "unit": "pressões/90",
        "higher_is_better": True,
        "group": "Pressão",
    },
    "shots_per90": {
        "label": "Finalizações/90",
        "desc": "Finalizações por 90 minutos.",
        "unit": "finalizações/90",
        "higher_is_better": True,
        "group": "Finalização",
    },
    "goals_per90": {
        "label": "Gols/90",
        "desc": "Gols marcados por 90 minutos.",
        "unit": "gols/90",
        "higher_is_better": True,
        "group": "Finalização",
    },
    "assists_per90": {
        "label": "Assistências/90",
        "desc": "Assistências por 90 minutos.",
        "unit": "assistências/90",
        "higher_is_better": True,
        "group": "Criação",
    },
    "minutes": {
        "label": "Minutos",
        "desc": "Minutos jogados na temporada.",
        "unit": "min",
        "higher_is_better": True,
        "group": "Volume",
    },
    "age": {
        "label": "Idade",
        "desc": "Idade do jogador.",
        "unit": "anos",
        "higher_is_better": False,
        "group": "Identidade",
    },
    "prospect_score": {
        "label": "Prospect Score",
        "desc": "Score combinando raridade e impacto: jogadores com perfil único e alto impacto.",
        "unit": "score",
        "higher_is_better": True,
        "group": "Outlier",
    },
    "rarity_score": {
        "label": "Rarity Score",
        "desc": "Quão raro é o perfil do jogador no espaço de features.",
        "unit": "score",
        "higher_is_better": True,
        "group": "Outlier",
    },
    "impact_score": {
        "label": "Impact Score",
        "desc": "Impacto estimado do jogador nas métricas de resultado.",
        "unit": "score",
        "higher_is_better": True,
        "group": "Outlier",
    },
    "cluster_id": {
        "label": "Cluster",
        "desc": "Grupo de jogadores com perfil similar (HDBSCAN).",
        "unit": "",
        "higher_is_better": None,
        "group": "Clustering",
    },
    "umap_x": {
        "label": "UMAP X",
        "desc": "Coordenada X na projeção UMAP (redução dimensional).",
        "unit": "",
        "higher_is_better": None,
        "group": "Clustering",
    },
    "umap_y": {
        "label": "UMAP Y",
        "desc": "Coordenada Y na projeção UMAP.",
        "unit": "",
        "higher_is_better": None,
        "group": "Clustering",
    },
    "position_group": {
        "label": "Posição",
        "desc": "Grupo de posição do jogador (GK, CB, FB, DM, CM_AM, W, ST).",
        "unit": "",
        "higher_is_better": None,
        "group": "Identidade",
    },
    "team": {
        "label": "Time",
        "desc": "Clube do jogador.",
        "unit": "",
        "higher_is_better": None,
        "group": "Identidade",
    },
    "season": {
        "label": "Temporada",
        "desc": "Temporada do Campeonato Brasileiro.",
        "unit": "",
        "higher_is_better": None,
        "group": "Identidade",
    },
    "player": {
        "label": "Jogador",
        "desc": "Nome do jogador.",
        "unit": "",
        "higher_is_better": None,
        "group": "Identidade",
    },
}


def get_metric_label(key: str) -> str:
    """Retorna label amigável da métrica."""
    return METRIC_INFO.get(key, {}).get("label", key)


def get_metric_desc(key: str) -> str:
    """Retorna descrição para tooltip/hover."""
    return METRIC_INFO.get(key, {}).get("desc", key)


def get_column_config_dict(columns: list[str]) -> dict[str, dict]:
    """
    Retorna dict {col: {label, help}} para o UI construir st.column_config.
    """
    return {
        col: {"label": METRIC_INFO.get(col, {}).get("label", col), "help": METRIC_INFO.get(col, {}).get("desc", "")}
        for col in columns
    }


def get_hovertemplate_suffix(metric_key: str) -> str:
    """Retorna sufixo para hovertemplate: descrição da métrica."""
    desc = get_metric_desc(metric_key)
    return f"<br>{desc}" if desc else ""
