import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Robô V2 - Live Analyzer",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise automática de futebol ao vivo")

API_URL = "https://v3.football.api-sports.io"

# ==============================
# API KEY
# ==============================

try:
    API_KEY = st.secrets["API_FOOTBALL_KEY"]
except Exception:
    API_KEY = ""

# ==============================
# CONSULTAR API
# ==============================

def consultar_api(endpoint, parametros=None):

    if not API_KEY:
        st.error("❌ API Key não encontrada nos Secrets do Streamlit.")
        return None

    try:
        resposta = requests.get(
            f"{API_URL}/{endpoint}",
            headers={
                "x-apisports-key": API_KEY
            },
            params=parametros,
            timeout=20
        )

        if resposta.status_code != 200:
            st.error(
                f"❌ Erro da API: HTTP {resposta.status_code}"
            )
            return None

        dados = resposta.json()

        if dados.get("errors"):
            st.error(
                f"❌ API: {dados['errors']}"
            )
            return None

        return dados

    except Exception as erro:
        st.error(
            f"❌ Erro de conexão: {erro}"
        )
        return None


# ==============================
# JOGOS AO VIVO
# ==============================

def buscar_jogos_ao_vivo():

    dados = consultar_api(
        "fixtures",
        {
            "live": "all"
        }
    )

    if not dados:
        return []

    return dados.get("response", [])


# ==============================
# ESTATÍSTICAS
# ==============================

def buscar_estatisticas(fixture_id):

    dados = consultar_api(
        "fixtures/statistics",
        {
            "fixture": fixture_id
        }
    )

    if not dados:
        return []

    return dados.get("response", [])


# ==============================
# EXTRAIR ESTATÍSTICAS
# ==============================

def extrair_estatisticas(dados):

    resultado = {
        "escanteios_casa": 0,
        "escanteios_fora": 0,
        "chutes_casa": 0,
        "chutes_fora": 0,
        "chutes_alvo_casa": 0,
        "chutes_alvo_fora": 0,
        "posse_casa": 0,
        "posse_fora": 0
    }

    if not dados or len(dados) < 2:
        return resultado

    for indice, equipe in enumerate(dados[:2]):

        estatisticas = equipe.get(
            "statistics",
            []
        )

        lado = "casa" if indice == 0 else "fora"

        for item in estatisticas:

            nome = str(
                item.get("type", "")
            ).lower()

            valor = item.get("value")

            if valor is None:
                continue

            # Escanteios
            if "corner" in nome:

                try:
                    resultado[
                        f"escanteios_{lado}"
                    ] = int(valor)
                except:
                    pass

            # Chutes
            elif nome == "total shots":

                try:
                    resultado[
                        f"chutes_{lado}"
                    ] = int(valor)
                except:
                    pass

            # Chutes no alvo
            elif "shots on goal" in nome:

                try:
                    resultado[
                        f"chutes_alvo_{lado}"
                    ] = int(valor)
                except:
                    pass

            # Posse
            elif "ball possession" in nome:

                try:
                    resultado[
                        f"posse_{lado}"
                    ] = int(
                        str(valor).replace("%", "")
                    )
                except:
                    pass

    return resultado


# ==============================
# ANALISAR JOGO
# ==============================

def analisar_jogo(jogo):

    fixture = jogo.get("fixture", {})
    teams = jogo.get("teams", {})
    goals = jogo.get("goals", {})

    fixture_id = fixture.get("id")

    casa = teams.get(
        "home",
        {}
    ).get(
        "name",
        "Casa"
    )

    fora = teams.get(
        "away",
        {}
    ).get(
        "name",
        "Fora"
    )

    placar_casa = goals.get("home") or 0
    placar_fora = goals.get("away") or 0

    status = fixture.get("status", {})

    minuto = status.get("elapsed") or 0

    # Estatísticas
    dados_stats = buscar_estatisticas(
        fixture_id
    )

    stats = extrair_estatisticas(
        dados_stats
    )

    escanteios_casa = stats[
        "escanteios_casa"
    ]

    escanteios_fora = stats[
        "escanteios_fora"
    ]

    escanteios_total = (
        escanteios_casa +
        escanteios_fora
    )

    chutes_total = (
        stats["chutes_casa"] +
        stats["chutes_fora"]
    )

    chutes_alvo_total = (
        stats["chutes_alvo_casa"] +
        stats["chutes_alvo_fora"]
    )

    gols_total = (
        placar_casa +
        placar_fora
    )

    # ==============================
    # PONTUAÇÃO
    # ==============================

    pontos = 0
    sinais = []

    if placar_casa == placar_fora:

        pontos += 10

        sinais.append(
            "⚖️ Jogo empatado"
        )

    if escanteios_total >= 4:

        pontos += 15

        sinais.append(
            "🚩 Volume de escanteios"
        )

    if escanteios_total >= 6:

        pontos += 20

        sinais.append(
            "🔥 Muitos escanteios"
        )

    if escanteios_total >= 8:

        pontos += 20

        sinais.append(
            "🚨 Volume muito alto de escanteios"
        )

    if chutes_total >= 10:

        pontos += 10

        sinais.append(
            "🎯 Muitos chutes"
        )

    if chutes_alvo_total >= 5:

        pontos += 15

        sinais.append(
            "🥅 Pressão com chutes no alvo"
        )

    if gols_total <= 1:

        pontos += 10

        sinais.append(
            "⚽ Poucos gols até agora"
        )

    # ==============================
    # NÍVEL
    # ==============================

    if pontos >= 60:

        nivel = "🔥 CHANCE QUENTE"

    elif pontos >= 40:

        nivel = "🟠 ATENÇÃO"

    elif pontos >= 25:

        nivel = "🟡 MONITORAR"

    else:

        nivel = "⚪ NORMAL"

    return {
        "id": fixture_id,
        "casa": casa,
        "fora": fora,
        "placar": f"{placar_casa} x {placar_fora}",
        "minuto": minuto,
        "escanteios": escanteios_total,
        "escanteios_casa": escanteios_casa,
        "escanteios_fora": escanteios_fora,
        "chutes": chutes_total,
        "chutes_alvo": chutes_alvo_total,
        "pontos": pontos,
        "nivel": nivel,
        "sinais": sinais
    }


# ==============================
# BOTÃO
# ==============================

if st.button(
    "🔄 ATUALIZAR JOGOS",
    use_container_width=True
):

    jogos = buscar_jogos_ao_vivo()

    st.session_state["jogos"] = jogos


# ==============================
# EXIBIÇÃO
# ==============================

if "jogos" not in st.session_state:

    st.info(
        "👆 Clique em 🔄 ATUALIZAR JOGOS"
    )

else:

    jogos = st.session_state["jogos"]

    if not jogos:

        st.warning(
            "⚽ Nenhum jogo ao vivo encontrado neste momento."
        )

    else:

        st.success(
            f"⚽ {len(jogos)} jogos ao vivo encontrados"
        )

        analises = []

        for jogo in jogos:

            try:

                analise = analisar_jogo(jogo)

                analises.append(analise)

            except Exception:

                continue

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
                    f"⏱️ {analise['minuto']}'"
                )

            with col2:

                st.metric(
                    "Placar",
                    analise["placar"]
                )

                st.metric(
                    "🚩 Escanteios",
                    analise["escanteios"]
                )

                st.write(
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
    "Robô V2 • "
    + datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)

st.warning(
    "⚠️ Esta ferramenta apresenta dados e "
    "análise estatística. Não garante resultados."
)