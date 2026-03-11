"""
Tab Explorer - scatter UMAP com clusters, AI insights, Player Intelligence Card.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data.loader import get_merged_df
from src.i18n.translations import t, get_metric_label, get_position_label
from src.ui.components import render_player_avatar
from src.ui.components.ai_button import render_ai_button
from src.ui.components.ai_modal import show_ai_insight
from src.ui.components.player_card import render_player_intelligence_card
from src.ui.theme import CLUSTER_COLORS, PLOTLY_TEMPLATE
from src.ai.insights import generate_explorer_insights

# Labels do gráfico por idioma
EXPLORER_TEXTS = {
    "pt": {
        "title": "Mapa de Jogadores",
        "subtitle": "Cada ponto = 1 jogador. Clique em um ponto para abrir o card em modal. Cores = grupos.",
        "players_shown": "jogadores exibidos", "cluster": "Grupo", "selected": "Selecionado",
        "axis1": "Dimensão 1", "axis2": "Dimensão 2",
        "ai_tooltip": "Clique para obter insights feitos por IA",
        "click_hint": "Clique em um ponto no gráfico para abrir o Player Intelligence Card.",
        "info_graph": """**Sobre o gráfico (UMAP)**
Cada ponto representa um jogador. O mapa usa UMAP para reduzir muitas métricas (xg/90, passes, tackles, etc.) em 2 eixos visíveis.

• **Eixos (Dimensão 1 e 2):** Coordenadas matemáticas do UMAP. Jogadores próximos têm perfis estatísticos similares.

• **Cores:** Grupos (clusters) identificados por HDBSCAN. Mesma cor = estilo de jogo parecido.

• **Proximidade:** Quanto mais perto no mapa, mais similar o perfil de jogo.""",
        "info_metrics": "**Métricas usadas**",
    },
    "en": {
        "title": "Player Map",
        "subtitle": "Each point = 1 player. Click a point to open the card in a modal. Colors = groups.",
        "players_shown": "players shown", "cluster": "Group", "selected": "Selected",
        "axis1": "Dimension 1", "axis2": "Dimension 2",
        "ai_tooltip": "Click to obtain AI-generated insights",
        "click_hint": "Click a point on the chart to open the Player Intelligence Card.",
        "info_graph": """**About the chart (UMAP)**
Each point represents one player. UMAP reduces many metrics (xg/90, passes, tackles, etc.) into 2 visible axes.

• **Axes (Dimension 1 & 2):** UMAP coordinates. Nearby players have similar statistical profiles.

• **Colors:** Clusters from HDBSCAN. Same color = similar playing style.

• **Proximity:** Closer on the map = more similar playing profile.""",
        "info_metrics": "**Metrics used**",
    },
    "es": {
        "title": "Mapa de Jugadores",
        "subtitle": "Cada punto = 1 jugador. Haz clic para abrir el card en modal. Colores = grupos.",
        "players_shown": "jugadores mostrados", "cluster": "Grupo", "selected": "Seleccionado",
        "axis1": "Dimensión 1", "axis2": "Dimensión 2",
        "ai_tooltip": "Clic para obtener insights generados por IA",
        "click_hint": "Haz clic en un punto para abrir el Player Intelligence Card.",
        "info_graph": """**Sobre el gráfico (UMAP)**
Cada punto representa un jugador. UMAP reduce muchas métricas en 2 ejes visibles.

• **Ejes:** Coordenadas del UMAP. Jugadores cercanos = perfiles similares.

• **Colores:** Clusters de HDBSCAN. Mismo color = estilo de juego parecido.

• **Proximidad:** Más cerca = perfil más similar.""",
        "info_metrics": "**Métricas usadas**",
    },
}

# Descrições das métricas (label: descrição)
METRIC_DESCRIPTIONS = {
    "pt": [
        ("xG/90", "Gols esperados por 90 min"),
        ("xA/90", "Assistências esperadas por 90 min"),
        ("Passes Prog./90", "Passes progressivos"),
        ("Conduções Prog./90", "Conduções progressivas"),
        ("Desarmes/90", "Desarmes por 90 min"),
        ("% Passes", "Percentual de acerto de passes"),
        ("Prospect Score", "Score de prospecto (raridade + impacto)"),
        ("Rarity Score", "Raridade do perfil vs. posição"),
        ("Impact Score", "Impacto das ações"),
    ],
    "en": [
        ("xG/90", "Expected goals per 90 min"),
        ("xA/90", "Expected assists per 90 min"),
        ("Prog. Passes/90", "Progressive passes"),
        ("Prog. Carries/90", "Progressive carries"),
        ("Tackles/90", "Tackles per 90 min"),
        ("Pass %", "Pass completion rate"),
        ("Prospect Score", "Prospect score (rarity + impact)"),
        ("Rarity Score", "Profile rarity vs. position"),
        ("Impact Score", "Impact of actions"),
    ],
    "es": [
        ("xG/90", "Goles esperados por 90 min"),
        ("xA/90", "Asistencias esperadas por 90 min"),
        ("Pases Prog./90", "Pases progresivos"),
        ("Conducciones Prog./90", "Conducciones progresivas"),
        ("Entradas/90", "Entradas por 90 min"),
        ("% Pases", "Porcentaje de pases"),
        ("Prospect Score", "Puntuación de prospecto"),
        ("Rarity Score", "Rareza del perfil"),
        ("Impact Score", "Impacto de acciones"),
    ],
}


def _txt(key: str) -> str:
    from src.i18n.translations import LOCALE
    return EXPLORER_TEXTS.get(LOCALE, EXPLORER_TEXTS["pt"]).get(key, key)


def render_explorer(df: pd.DataFrame, context: dict, images_df: pd.DataFrame = None):
    """Renderiza o scatter UMAP com visual melhorado."""
    if images_df is None:
        images_df = pd.DataFrame()

    if df.empty:
        st.warning(t("no_data"))
        return

    if "umap_x" not in df.columns or "umap_y" not in df.columns:
        st.warning("umap_x/umap_y não encontrados." if context.get("locale") == "pt" else "umap_x/umap_y not found.")
        return

    sub = df.copy()
    if "season" in sub.columns and context.get("season_list"):
        sub = sub[sub["season"].isin(context["season_list"])]
    if "position_group" in sub.columns:
        sub = sub[sub["position_group"] == context.get("position_group", "CM_AM")]
    if "age" in sub.columns and context.get("age_max"):
        sub = sub[sub["age"] <= context["age_max"]]
    if "minutes" in sub.columns and context.get("minutes_min"):
        sub = sub[sub["minutes"] >= context["minutes_min"]]
    if context.get("team"):
        sub = sub[sub["team"].isin(context["team"])]
    if context.get("cluster") and "cluster_id" in sub.columns:
        sub = sub[sub["cluster_id"].isin(context["cluster"])]

    if "player" not in sub.columns and "player_key" in sub.columns:
        sub = sub.rename(columns={"player_key": "player"})

    if sub.empty:
        st.warning(t("no_data") + " (filtros retornaram vazio)")
        return

    # Para o scatter: só pontos com UMAP válido (sub segue intacto para player_options)
    scatter_sub = sub.dropna(subset=["umap_x", "umap_y"])

    col_title, col_info = st.columns([20, 1])
    with col_title:
        st.markdown(f"### {_txt('title')}")
    def _render_info():
        st.markdown(_txt("info_graph"))
        st.markdown("---")
        st.markdown(_txt("info_metrics"))
        locale = context.get("locale", "pt")
        for label, desc in METRIC_DESCRIPTIONS.get(locale, METRIC_DESCRIPTIONS["pt"]):
            st.caption(f"• **{label}:** {desc}")

    with col_info:
        if hasattr(st, "popover"):
            with st.popover("ⓘ"):
                _render_info()
        else:
            with st.expander("ⓘ", expanded=False):
                _render_info()
    st.caption(_txt("subtitle"))

    # AI insight state - invalida quando filtros mudam
    filter_hash = f"{context.get('position_group','')}_{context.get('season_list',[])}_{context.get('team',[])}_{context.get('age_max','')}_{context.get('minutes_min','')}"
    key_status = "explorer_ai_status"
    key_text = "explorer_ai_text"
    key_filter = "explorer_ai_filter_hash"
    if key_filter not in st.session_state or st.session_state.get(key_filter) != filter_hash:
        st.session_state[key_filter] = filter_hash
        st.session_state[key_status] = "loading"
        st.session_state[key_text] = ""
    if key_text not in st.session_state:
        st.session_state[key_text] = ""

    # Player selection + Player Intelligence Card (renderiza PRIMEIRO)
    player_options = sorted(sub["player"].dropna().unique().tolist()) if "player" in sub.columns else []
    none_label = {"pt": "— Nenhum", "en": "— None", "es": "— Ninguno"}.get(context.get("locale", "pt"), "— None")
    player_selected = st.selectbox(t("select_player"), [none_label] + player_options, key="explorer_player") if player_options else None

    metric_cols = [c for c in sub.columns if "z_" in c or "per90" in c][:8]
    if not metric_cols:
        metric_cols = [c for c in sub.columns if sub[c].dtype in [np.float64, np.float32]][:8]

    if player_selected and player_selected != none_label:
        row = sub[sub["player"] == player_selected].iloc[0]
        render_player_intelligence_card(row, images_df, metric_cols, df, key_suffix="explorer")

    # Hover com labels traduzidos
    hover_cols = {}
    if "player" in sub.columns:
        hover_cols["player"] = True
    if "team" in sub.columns:
        hover_cols["team"] = True
    if "age" in sub.columns:
        hover_cols["age"] = True
    if "minutes" in sub.columns:
        hover_cols["minutes"] = True
    if "prospect_score" in sub.columns:
        hover_cols["prospect_score"] = ":.2f"

    color_col = "cluster_id" if "cluster_id" in sub.columns else None
    plot_df = scatter_sub if not scatter_sub.empty else sub
    if plot_df.empty:
        st.warning(t("no_data") + " (nenhum ponto com UMAP válido)")
        st.caption(f"{len(sub)} {_txt('players_shown')}.")
    else:
        # cluster_id como string para cores discretas; custom_data para capturar player no clique
        plot_df = plot_df.copy()
        if color_col and color_col in plot_df.columns:
            plot_df[color_col] = plot_df[color_col].astype(str)
        fig = px.scatter(
            plot_df, x="umap_x", y="umap_y", color=color_col,
            hover_data=hover_cols,
            custom_data=["player"] if "player" in plot_df.columns else None,
            title="",
            color_discrete_sequence=CLUSTER_COLORS if color_col else None,
            size_max=12,
        )
        fig.update_traces(marker=dict(size=18, opacity=0.9, line=dict(width=2, color="white")))
        fig.update_layout(
            height=550,
            xaxis_title=_txt("axis1"),
            yaxis_title=_txt("axis2"),
            legend_title=_txt("cluster"),
            margin=dict(t=20),
            **PLOTLY_TEMPLATE["layout"],
        )

        if player_selected and player_selected != none_label:
            sel_df = plot_df[plot_df["player"] == player_selected] if "player" in plot_df.columns else sub[sub["player"] == player_selected]
            if not sel_df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sel_df["umap_x"], y=sel_df["umap_y"], mode="markers",
                        marker=dict(size=18, symbol="star", color="gold", line=dict(width=2, color="black")),
                        name=f"{_txt('selected')}: {player_selected}",
                    )
                )

        # Gráfico com seleção de pontos; clique abre modal
        event = st.plotly_chart(
            fig, use_container_width=True,
            key="explorer_plot",
            on_select="rerun",
            selection_mode=["points"],
        )

        # Ao clicar em um ponto, abre modal com Player Card
        # Não abrir quando Chat está processando (sugestões ou envio) - evita modal indesejado
        skip_modal = st.session_state.pop("_chat_just_processed", False) or "pending_query" in st.session_state

        # Resetar "última seleção processada" quando filtros mudam (evita abrir card errado)
        _last_key = "_explorer_last_clicked_player"
        _filter_key = "_explorer_last_filter_hash"
        if st.session_state.get(_filter_key) != filter_hash:
            st.session_state[_filter_key] = filter_hash
            st.session_state[_last_key] = None

        player_clicked = None
        if not skip_modal:
            if event and hasattr(event, "selection") and event.selection and hasattr(event.selection, "points") and event.selection.points:
                # Usar só pontos do trace principal (curve 0 = scatter). O trace 1 é o overlay da estrela.
                for pt in event.selection.points:
                    curve = pt.get("curveNumber", pt.get("curve_number", 0))
                    if curve != 0:
                        continue
                    if pt.get("customdata") and len(pt["customdata"]) > 0:
                        player_clicked = str(pt["customdata"][0])
                        break

        # Só abrir modal para clique novo (não reabrir em reruns com mesma seleção persistente)
        last_clicked = st.session_state.get(_last_key)
        if player_clicked and player_clicked in player_options and player_clicked != last_clicked:
            st.session_state[_last_key] = player_clicked
            row = sub[sub["player"] == player_clicked].iloc[0]
            if hasattr(st, "dialog"):
                @st.dialog("Player Intelligence Card")
                def player_modal():
                    render_player_intelligence_card(row, images_df, metric_cols, df, key_suffix="explorer_modal")
                player_modal()
            else:
                with st.expander(f"🎯 {player_clicked}", expanded=True):
                    render_player_intelligence_card(row, images_df, metric_cols, df, key_suffix="explorer_modal")

    st.caption(f"{len(sub)} {_txt('players_shown')}. {_txt('click_hint')}")

    # AI insights: gera com dados de jogadores, times, posições, prospectos
    if st.session_state[key_status] == "loading":
        with st.spinner(_txt("ai_tooltip")):
            score_col = "prospect_score" if "prospect_score" in sub.columns else "rarity_score" if "rarity_score" in sub.columns else "minutes"
            top_pros = sub.nlargest(10, score_col)[["player", "team", score_col]]
            top_prospects = top_pros.to_string(index=False) if not top_pros.empty else "N/A"
            agg_team = {"player": "count"}
            if score_col in sub.columns:
                agg_team[score_col] = "max"
            by_team = sub.groupby("team").agg(agg_team).rename(columns={"player": "jogadores"}).head(15).to_string()
            by_pos = sub.groupby("position_group").agg(jogadores=("player", "count")).to_string() if "position_group" in sub.columns else "N/A"
            if "position_group" in sub.columns and score_col in sub.columns:
                pos_avg = sub.groupby("position_group")[score_col].mean()
                by_pos += "\nMédia score: " + pos_avg.to_string()
            pos_label = context.get("position_group", "—")
            seasons = context.get("season_list", [])
            filter_desc = f"Posição: {pos_label} | Temporada(s): {seasons} | Idade máx: {context.get('age_max', 23)} | Min: {context.get('minutes_min', 600)}"
            if context.get("team"):
                filter_desc += f" | Times: {context['team']}"
            st.session_state[key_text] = generate_explorer_insights(
                top_prospects, by_team, by_pos, filter_desc, locale=context.get("locale", "pt")
            )
            st.session_state[key_status] = "ready"
        st.rerun()

    if True:
        col_ai, _ = st.columns([1, 4])
        with col_ai:
            ai_clicked = render_ai_button(
                state=st.session_state[key_status],
                tooltip=_txt("ai_tooltip"),
                key="explorer_ai_btn",
            )
        if ai_clicked and st.session_state[key_status] == "ready":
            show_ai_insight(st.session_state[key_text], title="Key Insights")
