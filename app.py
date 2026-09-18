import streamlit as st
from datetime import datetime
from curl_cffi import requests

# ==============================
# CONFIGURAÇÃO
# ==============================

SOFASCORE_API = "https://api.sofascore.com/api/v1"

st.set_page_config(
    page_title="Robô V2 - Live Analyzer",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise automática de jogos ao vivo")

# ==============================
# SESSÃO SOFASCORE
# ==============================

def criar_sessao():
    return requests.Session(
        impersonate="chrome"
    )


# ==============================
# BUSCAR JOGOS AO VIVO
# ==============================

def buscar_jogos_ao_vivo():

    url = f"{SOFASCORE_API}/sport/football/events/live"

    try:

        sessao = criar_sessao()

        resposta = sessao.get(
            url,
            timeout=20,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.sofascore.com/",
                "Origin": "https://www.sofascore.com",
                "X-Requested-With": "XMLHttpRequest"
            }
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados.get("events", [])

    except Exception as erro:

        st.error(f"Erro ao buscar jogos: {erro}")

        return []


# ==============================
# BUSCAR ESTATÍSTICAS
# ==============================

def buscar_estatisticas(event_id):

    url = f"{SOFASCORE_API}/event/{event_id}/statistics"

    try:

        sessao = criar_sessao()

        resposta = sessao.get(
            url,
            timeout=15,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.sofascore.com/",
                "Origin": "https://www.sofascore.com",
                "X-Requested-With": "XMLHttpRequest"
            }
        )

        resposta.raise_for_status()

        return resposta.json()

    except Exception:

        return {}


# ==============================
# EXTRAIR ESCANTEIOS
# ==============================

def pegar_escanteios(dados):

    casa = 0
    fora = 0

    try:

        estatisticas = dados.get("statistics", [])

        for periodo in estatisticas:

            if periodo.get("period") != "ALL":
                continue

            grupos = periodo.get("groups", [])

            for grupo in grupos:

                itens = grupo.get("statisticsItems", [])

                for item in itens:

                    nome = str(item.get("name", "")).lower()

                    if "corner" in nome or "escante" in nome:

                        valor_casa = item.get("homeValue")
                        valor_fora = item.get("awayValue")

                        if valor_casa is None:
                            valor_casa = item.get("home", 0)

                        if valor_fora is None:
                            valor_fora = item.get("away", 0)

                        try:
                            casa = int(
                                str(valor_casa)
                                .replace("%", "")
                            )
                        except:
                            casa = 0

                        try:
                            fora = int(
                                str(valor_fora)
                                .replace("%", "")
                            )
                        except:
                            fora = 0

                        return casa, fora

    except Exception:
        pass

    return casa, fora


# ==============================
# ANÁLISE DO JOGO
# ==============================

def analisar_jogo(jogo):

    home = jogo.get("homeTeam", {})
    away = jogo.get("awayTeam", {})

    nome_casa = home.get("name", "Casa")
    nome_fora = away.get("name", "Fora")

    placar_casa = jogo.get(
        "homeScore", {}
    ).get("current", 0)

    placar_fora = jogo.get(
        "awayScore", {}
    ).get("current", 0)

    status = jogo.get("status", {})

    tempo = status.get(
        "description",
        "Ao vivo"
    )

    event_id = jogo.get("id")

    # --------------------------
    # ESTATÍSTICAS
    # --------------------------

    dados_estatisticas = buscar_estatisticas(
        event_id
    )

    escanteios_casa, escanteios_fora = pegar_escanteios(
        dados_estatisticas
    )

    escanteios_total = (
        escanteios_casa +
        escanteios_fora
    )

    # --------------------------
    # PONTUAÇÃO
    # --------------------------

    pontos = 0

    sinais = []

    gols = (
        placar_casa +
        placar_fora
    )

    # Jogo empatado
    if placar_casa == placar_fora:

        pontos += 10

        sinais.append(
            "⚖️ Jogo empatado"
        )

    # Muitos escanteios
    if escanteios_total >= 5:

        pontos += 25

        sinais.append(
            "🚩 Muitos escanteios"
        )

    # Pressão forte
    if escanteios_total >= 7:

        pontos += 20

        sinais.append(
            "🔥 Pressão forte em escanteios"
        )

    # Poucos gols
    if gols <= 1:

        pontos += 15

        sinais.append(
            "⚽ Poucos gols até agora"
        )

    # Jogo com muitos escanteios
    if escanteios_total >= 9:

        pontos += 15

        sinais.append(
            "🚨 Volume muito alto de escanteios"
        )

    # --------------------------
    # NÍVEL
    # --------------------------

    if pontos >= 60:

        nivel = "🔥 CHANCE QUENTE"

    elif pontos >= 40:

        nivel = "🟠 ATENÇÃO"

    elif pontos >= 25:

        nivel = "🟡 MONITORAR"

    else:

        nivel = "⚪ NORMAL"

    return {

        "id": event_id,

        "casa": nome_casa,

        "fora": nome_fora,

        "placar": f"{placar_casa} x {placar_fora}",

        "tempo": tempo,

        "escanteios_casa": escanteios_casa,

        "escanteios_fora": escanteios_fora,

        "escanteios": escanteios_total,

        "pontos": pontos,

        "nivel": nivel,

        "sinais": sinais

    }


# ==============================
# BOTÃO ATUALIZAR
# ==============================

if st.button(
    "🔄 ATUALIZAR JOGOS",
    use_container_width=True
):

    st.cache_data.clear()

    jogos = buscar_jogos_ao_vivo()

    st.session_state["jogos"] = jogos


# ==============================
# PRIMEIRO ACESSO
# ==============================

if "jogos" not in st.session_state:

    st.info(
        "Clique em 🔄 ATUALIZAR JOGOS para buscar partidas ao vivo."
    )


# ==============================
# MOSTRAR JOGOS
# ==============================

else:

    jogos = st.session_state["jogos"]

    if not jogos:

        st.warning(
            "Nenhum jogo ao vivo encontrado."
        )

    else:

        st.success(
            f"⚽ {len(jogos)} jogos encontrados ao vivo"
        )

        analises = []

        for jogo in jogos:

            try:

                analise = analisar_jogo(
                    jogo
                )

                analises.append(
                    analise
                )

            except Exception:
                continue

        # Ordenar pelas maiores pontuações

        analises.sort(
            key=lambda x: x["pontos"],
            reverse=True
        )

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

                st.caption(
                    f"Casa: {analise['escanteios_casa']} | "
                    f"Fora: {analise['escanteios_fora']}"
                )

            with col3:

                st.metric(
                    "Pontuação",
                    f"{analise['pontos']} / 100"
                )

                st.write(
                    analise["nivel"]
                )

            if analise["sinais"]:

                st.write(
                    "📊 **Sinais detectados:**"
                )

                for sinal in analise["sinais"]:

                    st.write(
                        f"- {sinal}"
                    )


# ==============================
# RODAPÉ
# ==============================

st.markdown("---")

st.caption(
    "Robô V2 • Última atualização: "
    + datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)

st.warning(
    "⚠️ O sistema apresenta análise estatística "
    "e não garante resultados."
)