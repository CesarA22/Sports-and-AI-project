"""
Tab Compare - comparação A vs B com placeholders, AI insights.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.i18n.translations import t, get_metric_label, get_position_label
from src.ui.components import render_player_avatar, get_image_url
from src.ui.components.ai_button import render_ai_button
from src.ui.components.ai_modal import show_ai_insight
from src.ai.insights import generate_comparison_insights

COMPARE_TEXTS = {
    "pt": {"photos_above": "Fotos dos jogadores", "vs": "vs", "comparison_table": "Comparação", "select_a": "Selecionar Jogador A", "select_b": "Selecionar Jogador B", "placeholder_card": "Escolha dois jogadores para comparar seus perfis estatísticos.", "ai_tooltip": "Clique para obter insights de scouting por IA"},
    "en": {"photos_above": "Player photos", "vs": "vs", "comparison_table": "Compare", "select_a": "Select Player A", "select_b": "Select Player B", "placeholder_card": "Choose two players to compare their statistical profiles.", "ai_tooltip": "Click to get AI scouting insights"},
    "es": {"photos_above": "Fotos de jugadores", "vs": "vs", "comparison_table": "Comparar", "select_a": "Seleccionar Jugador A", "select_b": "Seleccionar Jugador B", "placeholder_card": "Elige dos jugadores para comparar sus perfiles estadísticos.", "ai_tooltip": "Clic para obtener insights de scouting por IA"},
}


def _txt(key: str) -> str:
    from src.i18n.translations import LOCALE
    return COMPARE_TEXTS.get(LOCALE, COMPARE_TEXTS["pt"]).get(key, key)


def _radar_chart(row_a: pd.Series, row_b: pd.Series, metrics: list, locale: str) -> go.Figure:
    vals_a = [float(row_a.get(m, 0) or 0) for m in metrics]
    vals_b = [float(row_b.get(m, 0) or 0) for m in metrics]
    all_vals = vals_a + vals_b
    mx = max(all_vals) if all_vals else 1
    mn = min(all_vals) if all_vals else 0
    rng = mx - mn or 1
    vals_a_n = [(v - mn) / rng for v in vals_a]
    vals_b_n = [(v - mn) / rng for v in vals_b]
    vals_a_n = vals_a_n + [vals_a_n[0]]
    vals_b_n = vals_b_n + [vals_b_n[0]]
    labels = [get_metric_label(m) for m in metrics]
    categories = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_a_n, theta=categories, fill="toself", name=str(row_a.get("player", "A")), line=dict(color="#3b82f6")))
    fig.add_trace(go.Scatterpolar(r=vals_b_n, theta=categories, fill="toself", name=str(row_b.get("player", "B")), line=dict(color="#ef4444")))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=10))),
        showlegend=True, height=450, margin=dict(t=40),
    )
    return fig


def render_compare(df: pd.DataFrame, context: dict, images_df: pd.DataFrame = None):
    """Renderiza comparação com fotos em destaque."""
    if df.empty:
        st.warning(t("no_data"))
        return
    if images_df is None:
        images_df = pd.DataFrame()

    sub = df.copy()
    if "season" in sub.columns and context.get("season_list"):
        sub = sub[sub["season"].isin(context["season_list"])]
    if "position_group" in sub.columns:
        sub = sub[sub["position_group"] == context.get("position_group", "CM_AM")]

    # Opções únicas: "Nome (Time · Temp)" para evitar duplicatas
    pk = "player_key" if "player_key" in sub.columns else "player"
    if sub.empty or "player" not in sub.columns:
        st.warning(t("no_players"))
        return

    def _option_label(r):
        team = r.get("team", "")
        season = r.get("season", "")
        return f"{r['player']} ({team} · {season})"

    options = []
    key_to_row = {}
    for _, row in sub.drop_duplicates(subset=[pk]).iterrows():
        label = _option_label(row)
        options.append(label)
        key_to_row[label] = row

    if not options:
        st.warning(t("no_players"))
        return

    st.markdown(f"### {_txt('comparison_table')}")

    placeholder_a = _txt("select_a")
    placeholder_b = _txt("select_b")
    col1, col2 = st.columns(2)
    with col1:
        player_a_label = st.selectbox(t("player_a"), [placeholder_a] + options, key="compare_a")
    with col2:
        player_b_label = st.selectbox(t("player_b"), [placeholder_b] + options, key="compare_b")

    both_selected = (
        player_a_label and player_b_label
        and player_a_label != placeholder_a
        and player_b_label != placeholder_b
        and player_a_label != player_b_label
    )

    if not both_selected:
        st.info(_txt("placeholder_card"))
        render_ai_button(state="disabled", tooltip=_txt("ai_tooltip"), key="compare_ai_btn")
        return

    row_a = key_to_row.get(player_a_label)
    row_b = key_to_row.get(player_b_label)
    if row_a is None or row_b is None:
        st.warning(t("no_players"))
        return

    player_a = str(row_a.get("player", ""))
    player_b = str(row_b.get("player", ""))
    pk_a = row_a.get(pk, player_a)
    pk_b = row_b.get(pk, player_b)

    metric_cols = [c for c in sub.columns if "z_" in c or "per90" in c][:8]
    if not metric_cols:
        metric_cols = [c for c in sub.columns if sub[c].dtype in [np.float64, np.float32]][:8]
    metrics_text = "\n".join(
        f"- {get_metric_label(m)}: {player_a}={row_a.get(m, 0):.2f} | {player_b}={row_b.get(m, 0):.2f}"
        for m in metric_cols
    )

    col_ai, _ = st.columns([1, 4])
    with col_ai:
        ai_clicked = render_ai_button(state="ready", tooltip=_txt("ai_tooltip"), key="compare_ai_btn")
    if ai_clicked:
        with st.spinner("Gerando insights..."):
            insight = generate_comparison_insights(
                player_a, player_b, metrics_text, locale=context.get("locale", "pt")
            )
        show_ai_insight(insight, title="AI Scouting Insight")

    # Fotos grandes lado a lado
    st.markdown(f"**{_txt('photos_above')}**")
    c1, vs_col, c2 = st.columns([2, 1, 2])
    with c1:
        avatar_a = render_player_avatar(pk_a, player_a, images_df, 120)
        st.markdown(f'<div style="text-align:center;padding:10px">{avatar_a}<br><b>{player_a}</b><br><span style="color:#888">{row_a.get("team","")} • {get_position_label(str(row_a.get("position_group","")))}</span></div>', unsafe_allow_html=True)
    with vs_col:
        st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:180px;font-size:24px;font-weight:bold;color:#888">vs</div>', unsafe_allow_html=True)
    with c2:
        avatar_b = render_player_avatar(pk_b, player_b, images_df, 120)
        st.markdown(f'<div style="text-align:center;padding:10px">{avatar_b}<br><b>{player_b}</b><br><span style="color:#888">{row_b.get("team","")} • {get_position_label(str(row_b.get("position_group","")))}</span></div>', unsafe_allow_html=True)
    st.caption(t("image_source"))
    st.markdown("---")

    if metric_cols:
        fig = _radar_chart(row_a, row_b, metric_cols, context.get("locale", "pt"))
        st.plotly_chart(fig, use_container_width=True)

    comp_df = pd.DataFrame({
        t("metric"): [get_metric_label(m) for m in metric_cols],
        str(row_a.get("player", "A")): [row_a.get(m, "") for m in metric_cols],
        str(row_b.get("player", "B")): [row_b.get(m, "") for m in metric_cols],
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
