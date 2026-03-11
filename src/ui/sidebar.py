"""
Sidebar global - filtros compartilhados + seletor de idioma.
"""
import streamlit as st

from config import POSITION_GROUPS, SEASONS_ALLOWED
from src.i18n.translations import t, get_position_label, set_locale


def render_sidebar(teams_options=None, clusters_options=None):
    """Renderiza o sidebar com filtros e idioma."""
    lang = st.sidebar.selectbox("🌐 " + t("language"), ["pt", "en", "es"], format_func=lambda x: {"pt": "Português", "en": "English", "es": "Español"}[x])
    set_locale(lang)

    st.sidebar.title(t("app_title"))
    st.sidebar.markdown("---")

    season_opts = ["2024", "2023", t("both")]
    season_sel = st.sidebar.selectbox(t("season"), season_opts, index=0)
    if season_sel == t("both"):
        season = list(SEASONS_ALLOWED)
    else:
        season = [int(season_sel)] if season_sel.isdigit() else [2024]

    pos_labels = [f"{p} ({get_position_label(p)})" for p in POSITION_GROUPS]
    pos_idx = st.sidebar.selectbox(t("position"), range(len(POSITION_GROUPS)), format_func=lambda i: pos_labels[i], index=4)
    position_group = POSITION_GROUPS[pos_idx]

    age_max = st.sidebar.slider(t("age_max"), 18, 35, 23)
    minutes_min = st.sidebar.slider(t("minutes_min"), 0, 2000, 600)

    teams_opts = teams_options or []
    teams = st.sidebar.multiselect(t("teams"), options=teams_opts, default=[])

    cluster_opts = clusters_options or []
    cluster_filter = st.sidebar.multiselect(t("clusters"), options=cluster_opts, default=[])

    return {
        "season": season[0] if len(season) == 1 else season,
        "season_list": season,
        "position_group": position_group,
        "age_max": age_max,
        "minutes_min": minutes_min,
        "team": teams,
        "cluster": cluster_filter,
        "locale": lang,
    }
