import streamlit as st
import requests
from datetime import datetime

# ============================================================
# ROBÔ V2 - LIVE ANALYZER
# SofaScore + análise de jogos ao vivo
# ============================================================

st.set_page_config(
    page_title="Robô V2 - Live Analyzer",
    page_icon="⚽",
    layout="wide"
)

# ------------------------------------------------------------
# CONFIGURAÇÕES
# ------------------------------------------------------------

SOFASCORE_API = SOFASCORE_API = "https://api.sofascore.com/api/v1"

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise de jogos ao vivo usando dados do SofaScore")

# ------------------------------------------------------------
# FUNÇÃO PARA BUSCAR JOGOS AO VIVO
# ------------------------------------------------------------

def buscar_jogos_ao_vivo():
    url = f"{SOFASCORE_API}/sport/football/events/live"

    try:
        resposta = requests.get(
            url,
            timeout=10,
            headers={
                headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "X-Requested-With": "XMLHttpRequest"
}
            }
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get("events", [])

    except Exception as erro:
        st.error(f"Erro ao buscar jogos: {erro}")
        return []


# ------------------------------------------------------------
# ANÁLISE DO JOGO
# ------------------------------------------------------------

def analisar_jogo(jogo):

    home = jogo.get("homeTeam", {})
    away = jogo.get("awayTeam", {})

    nome_casa = home.get("name", "Casa")
    nome_fora = away.get("name", "Fora")

    placar = jogo.get("homeScore", {}).get("current", 0)
    placar_fora = jogo.get("awayScore", {}).get("current", 0)

    tempo = jogo.get("status", {}).get("type", "")

    minuto = jogo.get("status", {}).get("description", "")

    # --------------------------------------------------------
    # DADOS DE ESCANTEIOS
    # --------------------------------------------------------

    escanteios_casa = jogo.get("homeScore", {}).get(
        "period1Corners", 0
    )

    escanteios_fora = jogo.get("awayScore", {}).get(
        "period1Corners", 0
    )

    escanteios_total = (
        (escanteios_casa or 0) +
        (escanteios_fora or 0)
    )

    # --------------------------------------------------------
    # SISTEMA DE PONTUAÇÃO
    # --------------------------------------------------------

    pontos = 0
    sinais = []

    # Jogo empatado
    if placar == placar_fora:
        pontos += 10
        sinais.append("⚖️ Jogo empatado")

    # Muitos escanteios
    if escanteios_total >= 5:
        pontos += 25
        sinais.append("🚩 Muitos escanteios")

    if escanteios_total >= 7:
        pontos += 20
        sinais.append("🔥 Pressão forte em escanteios")

    # Jogo sem muitos gols
    gols = (placar or 0) + (placar_fora or 0)

    if gols <= 1:
        pontos += 15
        sinais.append("⚽ Poucos gols até agora")

    # Classificação
    if pontos >= 50:
        nivel = "🔥 CHANCE QUENTE"
    elif pontos >= 30:
        nivel = "🟡 ATENÇÃO"
    else:
        nivel = "⚪ NORMAL"

    return {
        "casa": nome_casa,
        "fora": nome_fora,
        "placar": f"{placar} x {placar_fora}",
        "tempo": minuto,
        "escanteios": escanteios_total,
        "pontos": pontos,
        "nivel": nivel,
        "sinais": sinais
    }


# ------------------------------------------------------------
# BOTÃO ATUALIZAR
# ------------------------------------------------------------

if st.button("🔄 ATUALIZAR JOGOS", use_container_width=True):

    st.cache_data.clear()

    jogos = buscar_jogos_ao_vivo()

    st.session_state["jogos"] = jogos


# ------------------------------------------------------------
# CARREGAR JOGOS
# ------------------------------------------------------------

if "jogos" not in st.session_state:

    st.info(
        "Clique em **ATUALIZAR JOGOS** para buscar partidas ao vivo."
    )

else:

    jogos = st.session_state["jogos"]

    if not jogos:

        st.warning("Nenhum jogo ao vivo encontrado.")

    else:

        st.success(
            f"⚽ {len(jogos)} jogos encontrados ao vivo"
        )

        # ----------------------------------------------------
        # ANALISAR TODOS OS JOGOS
        # ----------------------------------------------------

        analises = []

        for jogo in jogos:

            try:

                analise = analisar_jogo(jogo)

                analises.append(analise)

            except Exception:
                continue


        # ----------------------------------------------------
        # ORDENAR PELAS MAIORES PONTUAÇÕES
        # ----------------------------------------------------

        analises.sort(
            key=lambda x: x["pontos"],
            reverse=True
        )


        # ----------------------------------------------------
        # MOSTRAR RESULTADOS
        # ----------------------------------------------------

        for analise in analises:

            if analise["pontos"] < 20:
                continue

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.subheader(
                    f"🏟️ {analise['casa']} x {analise['fora']}"
                )

                st.write(
                    f"⏱️ {analise['tempo']}"
                )

            with col2:

                st.metric(
                    "Placar",
                    analise["placar"]
                )

                st.metric(
                    "Escanteios",
                    analise["escanteios"]
                )

            with col3:

                st.metric(
                    "Pontuação",
                    f"{analise['pontos']} / 100"
                )

                st.write(
                    analise["nivel"]
                )


            # ------------------------------------------------
            # SINAIS
            # ------------------------------------------------

            if analise["sinais"]:

                st.write("📊 **Sinais detectados:**")

                for sinal in analise["sinais"]:

                    st.write(
                        f"- {sinal}"
                    )


# ------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------

st.markdown("---")

st.caption(
    f"Robô V2 • Última atualização: "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)

st.warning(
    "⚠️ O sistema apresenta análise estatística e não garante resultados."
)