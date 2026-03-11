"""
AI Button - estados: loading, ready, disabled.
"""
import streamlit as st

# Ícone estrela (logo IA)
STAR_ICON = "✨"


def render_ai_button(
    state: str,  # "loading" | "ready" | "disabled"
    tooltip: str = "Clique para obter insights feitos por IA",
    key: str = "ai_btn",
) -> bool:
    """
    Renderiza botão IA. Retorna True se clicou (e state=ready).
    """
    if state == "loading":
        return st.button(
            f"{STAR_ICON} Gerando insights...",
            key=key,
            disabled=True,
            use_container_width=False,
        )
    if state == "disabled":
        return st.button(
            f"{STAR_ICON} AI Insights",
            key=key,
            disabled=True,
            use_container_width=False,
        )
    # ready
    return st.button(
        f"{STAR_ICON} AI Insights",
        key=key,
        help=tooltip,
        use_container_width=False,
    )
