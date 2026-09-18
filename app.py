import time
from datetime import datetime

import requests
import streamlit as st


# ============================================================
# ROBÔ V2 - LIVE ANALYZER
# ============================================================

st.set_page_config(
    page_title="Robô V2 - Análise ao Vivo",
    page_icon="⚽",
    layout="wide",
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_BASE = "https://www.sofascore.com/api/v1"

URL_JOGOS_AO_VIVO = (
    f"{URL_BASE}/sport/football/events/live"
)

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json",
}


# ============================================================
# BUSCAR JOGOS AO VIVO
# ============================================================

@st.cache_data(ttl=15)
def buscar_jogos_ao_vivo():

    try:

        resposta = requests.get(
            URL_JOGOS_AO_VIVO,
            headers=CABECALHOS,
            timeout=15,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get("events", []), None

    except requests.exceptions.Timeout:

        return [], "Tempo limite ao consultar o SofaScore."

    except requests.exceptions.RequestException as erro:

        return [], f"Erro de conexão: {erro}"

    except ValueError:

        return [], "Resposta inválida recebida do SofaScore."


# ============================================================
# TELA PRINCIPAL
# ============================================================

st.title("⚽ ROBÔ V2 — ANÁLISE AO VIVO")

st.markdown(
    """
### 🤖 Analisador de jogos em tempo real

Fonte de dados: **SofaScore**

O robô será preparado para analisar:

- ⚽ Gols
- 🚩 Escanteios
- 🟨 Cartões
- 🎯 Chutes
- 🔥 Pressão
- 🚨 Alertas
"""
)


# ============================================================
# BOTÃO DE ATUALIZAÇÃO
# ============================================================

if st.button(
    "🔄 ATUALIZAR JOGOS",
    use_container_width=True
):

    st.cache_data.clear()
    st.rerun()


# ============================================================
# BUSCAR JOGOS
# ============================================================

jogos, erro = buscar_jogos_ao_vivo()


if erro:

    st.error(
        f"❌ {erro}"
    )

else:

    st.success(
        f"🟢 {len(jogos)} jogos encontrados"
    )


# ============================================================
# MOSTRAR JOGOS
# ============================================================

if jogos:

    for jogo in jogos:

        casa = (
            jogo.get("homeTeam", {})
            .get("name", "Mandante")
        )

        fora = (
            jogo.get("awayTeam", {})
            .get("name", "Visitante")
        )

        placar_casa = (
            jogo.get("homeScore", {})
            .get("current", 0)
        )

        placar_fora = (
            jogo.get("awayScore", {})
            .get("current", 0)
        )

        st.divider()

        st.subheader(
            f"⚽ {casa}  {placar_casa} x "
            f"{placar_fora}  {fora}"
        )

else:

    st.info(
        "🟢 Neste momento não foram encontrados "
        "jogos de futebol ao vivo."
    )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Robô V2 • SofaScore • "
    + datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)