"""
AI Modal - exibe insight e armazena para contexto do Chat.
"""
import streamlit as st


def show_ai_insight(insight_text: str, title: str = "AI Scouting Insight"):
    """Exibe insight em expander e guarda em session_state para o Chat usar como contexto."""
    if "last_ai_insight" not in st.session_state:
        st.session_state["last_ai_insight"] = {}
    st.session_state["last_ai_insight"] = {"text": insight_text, "title": title}
    with st.expander(f"✨ **{title}**", expanded=True):
        st.markdown(insight_text)
