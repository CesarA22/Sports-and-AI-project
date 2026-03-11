"""
Constrói column_config para st.dataframe com labels traduzidos.
"""
import streamlit as st

from src.i18n.translations import get_metric_label, get_metric_desc


def build_column_config(
    columns: list[str],
    numeric_format: str = "%.2f",
) -> dict:
    """Gera column_config com labels e tooltips traduzidos."""
    config = {}
    int_cols = {"minutes", "age", "season", "cluster_id"}
    numeric_cols = {"xg_per90", "xa_per90", "prog_passes_per90", "prog_carries_per90", "tackles_per90",
        "pass_accuracy", "prospect_score", "rarity_score", "impact_score", "umap_x", "umap_y",
        "touches_box_per90", "interceptions_per90", "aerial_won_per90", "passes_completed_per90",
        "pressures_per90", "shots_per90", "goals_per90", "assists_per90",
    }
    for col in columns:
        label = get_metric_label(col)
        help_text = get_metric_desc(col) or ""
        if col in int_cols:
            config[col] = st.column_config.NumberColumn(label, help=help_text, format="%d")
        elif col in numeric_cols or "per90" in col or "score" in col or "accuracy" in col:
            config[col] = st.column_config.NumberColumn(label, help=help_text, format=numeric_format)
        else:
            config[col] = st.column_config.Column(label, help=help_text)
    return config


def build_column_config_simple(columns: list[str]) -> dict:
    """Versão simples: só label e help, sem type específico."""
    config = {}
    for col in columns:
        label = get_metric_label(col)
        help_text = get_metric_desc(col)
        config[col] = st.column_config.Column(label, help=help_text)
    return config
