import streamlit as st
import requests
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Robô V2 - Live Analyzer",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise automática de jogos de futebol ao vivo")

# ============================================================
# CONFIGURAÇÕES DO SOFASCORE
# ============================================================

LIVE_URL = "https://www.sofascore.com/api/v1/sport/football/events/live"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

MAX_JOGOS = 20

# ============================================================
# BUSCAR JOGOS AO VIVO
# ============================================================

def buscar_jogos():

    try:

        resposta = requests.get(
            LIVE_URL,
            headers=HEADERS,
            timeout=15
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get("events", [])

    except Exception as erro:

        st.error(f"Erro ao consultar o Sofascore: {erro}")

        return []


# ============================================================
# PEGAR ESTATÍSTICAS DO JOGO
# ============================================================

def buscar_estatisticas(event_id):

    url = (
        f"https://www.sofascore.com/api/v1/event/"
        f"{event_id}/statistics"
    )

    try:

        resposta = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if resposta.status_code != 200:
            return {}

        return resposta.json()

    except Exception:
        return {}


# ============================================================
# CALCULAR SINAIS
# ============================================================

def analisar_jogo(jogo):

    home = jogo.get("homeTeam", {}).get("name", "Casa")
    away = jogo.get("awayTeam", {}).get("name", "Fora")

    home_score = jogo.get("homeScore", {}).get("current", 0)
    away_score = jogo.get("awayScore", {}).get("current", 0)

    minuto = jogo.get("status", {}).get("period", "")

    tempo = jogo.get("status", {}).get("type", "")

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    gols = home_score + away_score

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = jogo.get("status", {}).get(
        "description",
        "Ao vivo"
    )

    # --------------------------------------------------------
    # INFORMAÇÕES BÁSICAS
    # --------------------------------------------------------

    return {
        "home": home,
        "away": away,
        "home_score": home_score,
        "away_score": away_score,
        "gols": gols,
        "status": status,
        "periodo": minuto,
        "tempo": tempo
    }


# ============================================================
# INTERFACE
# ============================================================

st.sidebar.header("⚙️ Configurações")

auto_atualizar = st.sidebar.checkbox(
    "🔄 Atualização automática",
    value=False
)

if st.sidebar.button("🔄 Atualizar agora"):

    st.rerun()


# ============================================================
# HORA DA CONSULTA
# ============================================================

hora = datetime.now().strftime("%H:%M:%S")

st.info(
    f"🕐 Última atualização: {hora}"
)


# ============================================================
# BUSCAR JOGOS
# ============================================================

with st.spinner("Buscando jogos ao vivo..."):

    jogos = buscar_jogos()


# ============================================================
# RESULTADO
# ============================================================

if not jogos:

    st.warning(
        "⚠️ Nenhum jogo ao vivo encontrado no momento."
    )

else:

    st.success(
        f"⚽ {len(jogos)} jogos encontrados"
    )

    st.divider()

    # Limita quantidade de jogos exibidos
    jogos = jogos[:MAX_JOGOS]

    for jogo in jogos:

        analise = analisar_jogo(jogo)

        event_id = jogo.get("id")

        home = analise["home"]
        away = analise["away"]

        home_score = analise["home_score"]
        away_score = analise["away_score"]

        gols = analise["gols"]

        status = analise["status"]

        # ====================================================
        # CARTÃO DO JOGO
        # ====================================================

        st.subheader(
            f"⚽ {home}  {home_score} x "
            f"{away_score}  {away}"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Placar",
                f"{home_score} x {away_score}"
            )

        with col2:

            st.metric(
                "Gols",
                gols
            )

        with col3:

            st.metric(
                "Status",
                status
            )

        with col4:

            if event_id:

                st.write(
                    f"ID: {event_id}"
                )

        # ====================================================
        # ANÁLISE INICIAL
        # ====================================================

        if gols == 0:

            st.warning(
                "🟡 Jogo sem gols até o momento."
            )

        elif gols >= 1:

            st.success(
                "🟢 Jogo já teve gol."
            )

        # ====================================================
        # ESTATÍSTICAS
        # ====================================================

        if event_id:

            with st.expander(
                "📊 Ver estatísticas"
            ):

                estatisticas = buscar_estatisticas(
                    event_id
                )

                if estatisticas:

                    st.json(estatisticas)

                else:

                    st.info(
                        "Estatísticas ainda não disponíveis."
                    )

        st.divider()


# ============================================================
# RODAPÉ
# ============================================================

st.caption(
    "Robô V2 • Dados de partidas do Sofascore • "
    "Ferramenta experimental de análise esportiva"
)