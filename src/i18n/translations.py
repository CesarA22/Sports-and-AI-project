"""
i18n - Traduções PT-BR, EN, ES.
"""

LOCALE = "pt"  # default

TRANSLATIONS = {
    "pt": {
        "app_title": "Scout Radar",
        "season": "Temporada",
        "position": "Posição",
        "age_max": "Idade máx. (U-23)",
        "minutes_min": "Min. jogados",
        "teams": "Time(s)",
        "clusters": "Cluster(s)",
        "both": "Ambas",
        "explorer": "Explorador",
        "outliers": "Outliers",
        "compare": "Comparar",
        "chat": "Chat (Grounded)",
        "select_player": "Selecionar jogador",
        "player_a": "Jogador A",
        "player_b": "Jogador B",
        "select_two": "Selecione dois jogadores diferentes.",
        "metric": "Métrica",
        "image_source": "Fonte das imagens: Wikimedia Commons",
        "no_data": "Nenhum dado carregado.",
        "no_players": "Nenhum jogador disponível nos filtros.",
        "language": "Idioma",
        "top_k": "Top {k} por {metric}",
        "none": "Nenhum",
    },
    "en": {
        "app_title": "Scout Radar",
        "season": "Season",
        "position": "Position",
        "age_max": "Max age (U-23)",
        "minutes_min": "Min. played",
        "teams": "Team(s)",
        "clusters": "Cluster(s)",
        "both": "Both",
        "explorer": "Explorer",
        "outliers": "Outliers",
        "compare": "Compare",
        "chat": "Chat (Grounded)",
        "select_player": "Select player",
        "player_a": "Player A",
        "player_b": "Player B",
        "select_two": "Select two different players.",
        "metric": "Metric",
        "image_source": "Image source: Wikimedia Commons",
        "no_data": "No data loaded.",
        "no_players": "No players available in filters.",
        "language": "Language",
        "top_k": "Top {k} by {metric}",
        "none": "None",
    },
    "es": {
        "app_title": "Scout Radar",
        "season": "Temporada",
        "position": "Posición",
        "age_max": "Edad máx. (U-23)",
        "minutes_min": "Min. jugados",
        "teams": "Equipo(s)",
        "clusters": "Cluster(s)",
        "both": "Ambas",
        "explorer": "Explorador",
        "outliers": "Outliers",
        "compare": "Comparar",
        "chat": "Chat (Grounded)",
        "select_player": "Seleccionar jugador",
        "player_a": "Jugador A",
        "player_b": "Jugador B",
        "select_two": "Selecciona dos jugadores diferentes.",
        "metric": "Métrica",
        "image_source": "Fuente de imágenes: Wikimedia Commons",
        "no_data": "Sin datos cargados.",
        "no_players": "Ningún jugador disponible en filtros.",
        "language": "Idioma",
        "top_k": "Top {k} por {metric}",
        "none": "Ninguno",
    },
}

# Labels de posições por idioma
POS_LABELS = {
    "pt": {
        "GK": "Goleiro",
        "CB": "Zagueiro Central",
        "FB": "Lateral",
        "DM": "Volante",
        "CM_AM": "Meio-Campo / Meia",
        "W": "Ponta",
        "ST": "Atacante",
    },
    "en": {
        "GK": "Goalkeeper",
        "CB": "Centre Back",
        "FB": "Full Back",
        "DM": "Defensive Midfielder",
        "CM_AM": "Central / Attacking Midfielder",
        "W": "Winger",
        "ST": "Striker",
    },
    "es": {
        "GK": "Portero",
        "CB": "Defensa Central",
        "FB": "Lateral",
        "DM": "Mediocampista Defensivo",
        "CM_AM": "Mediocampista / Mediapunta",
        "W": "Extremo",
        "ST": "Delantero",
    },
}

# Métricas por idioma
METRIC_LABELS = {
    "pt": {
        "xg_per90": ("xG/90", "Gols esperados por 90 min"),
        "xa_per90": ("xA/90", "Assistências esperadas por 90 min"),
        "prog_passes_per90": ("Passes Prog./90", "Passes progressivos"),
        "prog_carries_per90": ("Conduções Prog./90", "Conduções progressivas"),
        "tackles_per90": ("Desarmes/90", "Desarmes por 90 min"),
        "pass_accuracy": ("% Passes", "Percentual de passes"),
        "prospect_score": ("Prospect Score", "Score de prospecto"),
        "rarity_score": ("Rarity Score", "Raridade do perfil"),
        "impact_score": ("Impact Score", "Impacto"),
        "minutes": ("Minutos", "Minutos jogados"),
        "age": ("Idade", "Idade"),
        "cluster_id": ("Cluster", "Grupo de similaridade"),
        "player": ("Jogador", "Nome"),
        "team": ("Time", "Clube"),
        "season": ("Temporada", "Ano"),
        "position_group": ("Posição", "Posição em campo"),
        "foto": ("Foto", "Imagem do jogador"),
    },
    "en": {
        "xg_per90": ("xG/90", "Expected goals per 90 min"),
        "xa_per90": ("xA/90", "Expected assists per 90 min"),
        "prog_passes_per90": ("Prog. Passes/90", "Progressive passes"),
        "prog_carries_per90": ("Prog. Carries/90", "Progressive carries"),
        "tackles_per90": ("Tackles/90", "Tackles per 90 min"),
        "pass_accuracy": ("Pass %", "Pass completion rate"),
        "prospect_score": ("Prospect Score", "Prospect score"),
        "rarity_score": ("Rarity Score", "Profile rarity"),
        "impact_score": ("Impact Score", "Impact"),
        "minutes": ("Minutes", "Minutes played"),
        "age": ("Age", "Age"),
        "cluster_id": ("Cluster", "Similarity group"),
        "player": ("Player", "Name"),
        "team": ("Team", "Club"),
        "season": ("Season", "Year"),
        "position_group": ("Position", "Field position"),
        "foto": ("Photo", "Player image"),
    },
    "es": {
        "xg_per90": ("xG/90", "Goles esperados por 90 min"),
        "xa_per90": ("xA/90", "Asistencias esperadas por 90 min"),
        "prog_passes_per90": ("Pases Prog./90", "Pases progresivos"),
        "prog_carries_per90": ("Conducciones Prog./90", "Conducciones progresivas"),
        "tackles_per90": ("Entradas/90", "Entradas por 90 min"),
        "pass_accuracy": ("% Pases", "Porcentaje de pases"),
        "prospect_score": ("Prospect Score", "Puntuación de prospecto"),
        "rarity_score": ("Rarity Score", "Rareza del perfil"),
        "impact_score": ("Impact Score", "Impacto"),
        "minutes": ("Minutos", "Minutos jugados"),
        "age": ("Edad", "Edad"),
        "cluster_id": ("Cluster", "Grupo de similitud"),
        "player": ("Jugador", "Nombre"),
        "team": ("Equipo", "Club"),
        "season": ("Temporada", "Año"),
        "position_group": ("Posición", "Posición en campo"),
        "foto": ("Foto", "Imagen del jugador"),
    },
}


def set_locale(locale: str):
    global LOCALE
    LOCALE = locale if locale in TRANSLATIONS else "pt"


def t(key: str, **kwargs) -> str:
    s = TRANSLATIONS.get(LOCALE, TRANSLATIONS["pt"]).get(key, key)
    return s.format(**kwargs) if kwargs else s


def get_position_label(pos: str) -> str:
    return POS_LABELS.get(LOCALE, POS_LABELS["pt"]).get(pos, pos)


def get_metric_label(metric_key: str) -> str:
    m = METRIC_LABELS.get(LOCALE, METRIC_LABELS["pt"]).get(metric_key)
    if m:
        return m[0]
    # Fallback: formata key (xg_per90 -> xG/90)
    key = str(metric_key).replace("_", " ").title()
    if "per90" in metric_key:
        key = metric_key.replace("_per90", "/90").replace("_", " ").title()
    return key


def get_metric_desc(metric_key: str) -> str:
    m = METRIC_LABELS.get(LOCALE, METRIC_LABELS["pt"]).get(metric_key)
    return m[1] if m and len(m) > 1 else ""
