    import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Robô V2 - Análise de Futebol",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Robô V2 — Análise de Jogos ao Vivo")
st.caption("Sistema de análise estatística em tempo real")

st.divider()

# Configurações
st.sidebar.header("⚙️ Configurações")

api_url = st.sidebar.text_input(
    "URL da API",
    value="https://www.thesportsdb.com/api/v1/json/3"
)

st.sidebar.info(
    "O Robô V2 analisa estatísticas dos jogos e gera indicadores. "
    "Ele não realiza apostas automaticamente."
)

# Busca de jogos
st.subheader("🔴 Jogos ao vivo")

if st.button("🔄 Atualizar jogos", use_container_width=True):

    try:
        url = f"{api_url}/eventsday.php?d={datetime.now().strftime('%Y-%m-%d')}"
        resposta = requests.get(url, timeout=10)

        if resposta.status_code == 200:
            dados = resposta.json()
            jogos = dados.get("events") or []

            if not jogos:
                st.warning("Nenhum jogo encontrado para hoje.")
            else:
                st.success(f"{len(jogos)} jogos encontrados.")

                for jogo in jogos:
                    mandante = jogo.get("strHomeTeam", "Mandante")
                    visitante = jogo.get("strAwayTeam", "Visitante")
                    placar_casa = jogo.get("intHomeScore") or 0
                    placar_fora = jogo.get("intAwayScore") or 0
                    status = jogo.get("strStatus", "Não informado")

                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 3])

                        with col1:
                            st.write(f"**{mandante}**")

                        with col2:
                            st.markdown(
                                f"### {placar_casa} × {placar_fora}"
                            )

                        with col3:
                            st.write(f"**{visitante}**")

                        st.caption(f"Status: {status}")

        else:
            st.error("Erro ao consultar a API.")

    except Exception as erro:
        st.error(f"Erro: {erro}")

else:
    st.info("Clique em **Atualizar jogos** para carregar os jogos.")

st.divider()

st.subheader("📊 Análise")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Jogos analisados", "0")

with col2:
    st.metric("Sinais encontrados", "0")

with col3:
    st.metric("Atualização", "Manual")

st.caption("Robô V2 — módulo inicial")