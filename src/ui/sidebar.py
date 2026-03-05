"""
Sidebar global - filtros compartilhados entre Visualizer e Chat.
"""
import streamlit as st

from config import POSITION_GROUPS, SEASONS_ALLOWED


def render_sidebar(teams_options=None, clusters_options=None):
    """Renderiza o sidebar com filtros. teams_options e clusters_options vêm do DataFrame."""
    st.sidebar.title("Scout Radar")
    st.sidebar.markdown("---")

    season_opts = ["2024", "2023", "Ambas"]
    season_sel = st.sidebar.selectbox("Temporada", season_opts, index=0)
    if season_sel == "Ambas":
        season = list(SEASONS_ALLOWED)
    else:
        season = [int(season_sel)]

    position_group = st.sidebar.selectbox(
        "Posição",
        POSITION_GROUPS,
        index=4,  # CM_AM default
    )

    age_max = st.sidebar.slider("Idade máx. (U-23)", 18, 35, 23)
    minutes_min = st.sidebar.slider("Min. jogados", 0, 2000, 600)

    # Team filter (multi)
    teams_opts = teams_options or []
    teams = st.sidebar.multiselect("Time(s)", options=teams_opts, default=[])

    cluster_opts = clusters_options or []
    cluster_filter = st.sidebar.multiselect("Cluster(s)", options=cluster_opts, default=[])

    return {
        "season": season[0] if len(season) == 1 else season,
        "season_list": season,
        "position_group": position_group,
        "age_max": age_max,
        "minutes_min": minutes_min,
        "team": teams,
        "cluster": cluster_filter,
    }
