"""
Design system - Dark AI scouting theme.
"""
# Cores principais
BG_PRIMARY = "#0B0B12"
BG_SECONDARY = "#11111B"
BG_CARD = "#161622"
BORDER = "#232334"
TEXT_PRIMARY = "#E6E6F0"
TEXT_SECONDARY = "#9CA3AF"

# Gradiente IA
GRADIENT_AI = "linear-gradient(135deg, #C026D3, #7C3AED, #22D3EE)"
GRADIENT_BTN = "linear-gradient(135deg, #9333EA, #6366F1, #22D3EE)"

# Paleta clusters (Plotly)
CLUSTER_COLORS = ["#A855F7", "#7C3AED", "#6366F1", "#22D3EE", "#E879F9", "#9333EA"]

# Plotly template dark
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": TEXT_SECONDARY, "family": "sans-serif"},
        "xaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER},
        "yaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER},
        "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": TEXT_PRIMARY}},
        "colorway": CLUSTER_COLORS,
    }
}
