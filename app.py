"""
Scout Radar - Streamlit App
Visualizer (UMAP, clusters, outliers, compare) + Chatbot grounded.
"""
import sys
from pathlib import Path

# Garantir que o project root está no path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.data.loader import load_data, get_merged_df
from src.ui.sidebar import render_sidebar
from src.ui.explorer import render_explorer
from src.ui.outliers import render_outliers
from src.ui.compare import render_compare
from src.ui.chat_tab import render_chat_tab


def main():
    st.set_page_config(page_title="Scout Radar", page_icon="⚽", layout="wide")

    # Carregar dados
    data = load_data()
    df = get_merged_df(data)

    # Opções para filtros (teams, clusters)
    teams_opts = sorted(df["team"].dropna().unique().tolist()) if not df.empty and "team" in df.columns else []
    clusters_opts = sorted(df["cluster_id"].dropna().unique().astype(int).tolist()) if not df.empty and "cluster_id" in df.columns else []

    # Sidebar
    context = render_sidebar(teams_options=teams_opts, clusters_options=clusters_opts)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Explorer", "Outliers", "Compare", "Chat (Grounded)"])

    with tab1:
        render_explorer(df, context)

    with tab2:
        render_outliers(df, context)

    with tab3:
        render_compare(df, context)

    with tab4:
        render_chat_tab(data, context)


if __name__ == "__main__":
    main()
