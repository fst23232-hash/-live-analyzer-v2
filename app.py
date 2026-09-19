import streamlit as st
import requests
from datetime import datetime
import time

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Robô V2 - Live Analyzer",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise automática de futebol ao vivo com dados do SofaScore")

BASE_URL = "https://www.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

MAX_JOGOS = 30


# ============================================================
# FUNÇÃO GENÉRICA DE REQUISIÇÃO
# ============================================================

def requisicao(url):

    try:
        resposta = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        if resposta.status_code == 200:
            return resposta.json()

        return {}

    except Exception:
        return {}


# ============================================================
# JOGOS AO VIVO
# ============================================================

def buscar_jogos_ao_vivo():

    url = f"{BASE_URL}/sport/football/events/live"

    dados = requisicao(url)

    return dados.get("events", [])


# ============================================================
# ESTATÍSTICAS
# ============================================================

def buscar_estatisticas(event_id):

    url = f"{BASE_URL}/event/{event_id}/statistics"

    dados = requisicao(url)

    resultado = {}

    for periodo in dados.get("statistics", []):

        if periodo.get("period") != "ALL":
            continue

        for grupo in periodo.get("groups", []):

            for item in grupo.get("statisticsItems", []):

                nome = item.get("name", "")

                resultado[nome] = {
                    "home": item.get("home"),
                    "away": item.get("away")
                }

    return resultado


# ============================================================
# INCIDENTES
# ============================================================

def buscar_incidentes(event_id):

    url = f"{BASE_URL}/event/{event_id}/incidents"

    dados = requisicao(url)

    return dados.get("incidents", [])


# ============================================================
# MOMENTUM
# ============================================================

def buscar_momentum(event_id):

    url = f"{BASE_URL}/event/{event_id}/graph"

    dados = requisicao(url)

    return dados.get("graphPoints", [])


# ============================================================
# CONVERTER NÚMEROS
# ============================================================

def numero(valor):

    if valor is None:
        return 0.0

    try:

        texto = str(valor)

        texto = texto.replace("%", "")
        texto = texto.replace(",", ".")

        return float(texto)

    except Exception:

        return 0.0


# ============================================================
# PEGAR ESTATÍSTICA
# ============================================================

def pegar_stat(estatisticas, nomes):

    for nome in nomes:

        if nome in estatisticas:

            dados = estatisticas[nome]

            return (
                numero(dados.get("home")),
                numero(dados.get("away"))
            )

    return 0.0, 0.0


# ============================================================
# ANÁLISE DO JOGO
# ============================================================

def analisar_jogo(jogo):

    home = jogo.get(
        "homeTeam", {}
    ).get(
        "name",
        "Casa"
    )

    away = jogo.get(
        "awayTeam", {}
    ).get(
        "name",
        "Fora"
    )

    home_score = jogo.get(
        "homeScore", {}
    ).get(
        "current",
        0
    )

    away_score = jogo.get(
        "awayScore", {}
    ).get(
        "current",
        0
    )

    status = jogo.get(
        "status", {}
    )

    minuto = status.get(
        "currentPeriodStartTimestamp"
    )

    descricao = status.get(
        "description",
        "Ao vivo"
    )

    return {
        "home": home,
        "away": away,
        "home_score": home_score,
        "away_score": away_score,
        "status": descricao,
        "timestamp": minuto
    }


# ============================================================
# ÍNDICE DE PRESSÃO
# ============================================================

def calcular_pressao(estatisticas, momentum):

    finalizacoes = pegar_stat(
        estatisticas,
        [
            "Total shots",
            "Shots"
        ]
    )

    no_alvo = pegar_stat(
        estatisticas,
        [
            "Shots on target"
        ]
    )

    escanteios = pegar_stat(
        estatisticas,
        [
            "Corner kicks"
        ]
    )

    grandes_chances = pegar_stat(
        estatisticas,
        [
            "Big chances"
        ]
    )

    ataques_perigosos = pegar_stat(
        estatisticas,
        [
            "Dangerous attacks"
        ]
    )

    posse = pegar_stat(
        estatisticas,
        [
            "Ball possession"
        ]
    )

    # --------------------------------------------------------
    # PONTUAÇÃO
    # --------------------------------------------------------

    casa = (
        finalizacoes[0] * 2
        + no_alvo[0] * 4
        + escanteios[0] * 2
        + grandes_chances[0] * 5
        + ataques_perigosos[0] * 0.15
    )

    fora = (
        finalizacoes[1] * 2
        + no_alvo[1] * 4
        + escanteios[1] * 2
        + grandes_chances[1] * 5
        + ataques_perigosos[1] * 0.15
    )

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    if momentum:

        ultimos = momentum[-10:]

        soma = 0

        for ponto in ultimos:

            soma += numero(
                ponto.get("value", 0)
            )

        if soma > 0:
            casa += min(soma * 0.15, 15)

        elif soma < 0:
            fora += min(abs(soma) * 0.15, 15)

    # --------------------------------------------------------
    # POSSE
    # --------------------------------------------------------

    if posse[0] > posse[1]:

        casa += min(
            (posse[0] - posse[1]) * 0.10,
            5
        )

    elif posse[1] > posse[0]:

        fora += min(
            (posse[1] - posse[0]) * 0.10,
            5
        )

    total = casa + fora

    if total <= 0:

        return 0, 0

    percentual_casa = round(
        (casa / total) * 100
    )

    percentual_fora = round(
        (fora / total) * 100
    )

    return percentual_casa, percentual_fora


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def classificar_pressao(maior):

    if maior >= 80:

        return (
            "🔥🔥 MUITO ALTA",
            "danger"
        )

    if maior >= 70:

        return (
            "🔥 ALTA",
            "warning"
        )

    if maior >= 55:

        return (
            "🟡 MODERADA",
            "moderate"
        )

    return (
        "🔵 BAIXA",
        "low"
    )


# ============================================================
# CONTAR CARTÕES
# ============================================================

def contar_cartoes(incidentes):

    casa = 0
    fora = 0

    for incidente in incidentes:

        if incidente.get("incidentType") != "card":
            continue

        classe = incidente.get(
            "incidentClass",
            ""
        )

        if classe not in [
            "yellow",
            "yellowRed",
            "red"
        ]:
            continue

        if incidente.get("isHome"):

            casa += 1

        else:

            fora += 1

    return casa, fora


# ============================================================
# INTERFACE LATERAL
# ============================================================

st.sidebar.header("⚙️ CONFIGURAÇÕES")

auto = st.sidebar.checkbox(
    "🔄 Atualização automática",
    value=False
)

intervalo = st.sidebar.slider(
    "Intervalo de atualização",
    min_value=15,
    max_value=120,
    value=30,
    step=15
)

mostrar_estatisticas = st.sidebar.checkbox(
    "📊 Mostrar estatísticas",
    value=True
)

mostrar_incidentes = st.sidebar.checkbox(
    "🟨 Mostrar cartões",
    value=True
)

mostrar_momentum = st.sidebar.checkbox(
    "📈 Mostrar momentum",
    value=True
)

if st.sidebar.button("🔄 ATUALIZAR AGORA"):

    st.rerun()


# ============================================================
# HORA
# ============================================================

hora = datetime.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

st.info(
    f"🕐 Última atualização: {hora}"
)


# ============================================================
# BUSCAR JOGOS
# ============================================================

with st.spinner(
    "🔎 Procurando jogos ao vivo..."
):

    jogos = buscar_jogos_ao_vivo()


# ============================================================
# SEM JOGOS
# ============================================================

if not jogos:

    st.warning(
        "⚠️ Nenhum jogo de futebol ao vivo "
        "foi encontrado neste momento."
    )

    st.caption(
        "Quando houver partidas ao vivo, "
        "elas aparecerão automaticamente aqui."
    )


# ============================================================
# JOGOS ENCONTRADOS
# ============================================================

else:

    st.success(
        f"⚽ {len(jogos)} jogos ao vivo encontrados"
    )

    st.divider()

    jogos = jogos[:MAX_JOGOS]

    for jogo in jogos:

        event_id = jogo.get("id")

        analise = analisar_jogo(jogo)

        home = analise["home"]
        away = analise["away"]

        placar_home = analise["home_score"]
        placar_away = analise["away_score"]

        status = analise["status"]

        # ====================================================
        # CABEÇALHO
        # ====================================================

        st.markdown(
            f"## ⚽ {home} "
            f"**{placar_home} x {placar_away}** "
            f"{away}"
        )

        st.caption(
            f"⏱️ {status}   |   ID: {event_id}"
        )

        # ====================================================
        # BUSCAR DADOS
        # ====================================================

        estatisticas = buscar_estatisticas(
            event_id
        )

        incidentes = buscar_incidentes(
            event_id
        )

        momentum = buscar_momentum(
            event_id
        )

        # ====================================================
        # PRESSÃO
        # ====================================================

        pressao_home, pressao_away = (
            calcular_pressao(
                estatisticas,
                momentum
            )
        )

        maior_pressao = max(
            pressao_home,
            pressao_away
        )

        if pressao_home >= pressao_away:

            time_pressao = home

        else:

            time_pressao = away

        classificacao, tipo = classificar_pressao(
            maior_pressao
        )

        # ====================================================
        # MÉTRICAS PRINCIPAIS
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                f"🏠 {home}",
                f"{pressao_home}%"
            )

        with col2:

            st.metric(
                f"✈️ {away}",
                f"{pressao_away}%"
            )

        with col3:

            st.metric(
                "🔥 Pressão",
                classificacao
            )

        with col4:

            st.metric(
                "🎯 Líder",
                time_pressao
            )

        # ====================================================
        # BARRA
        # ====================================================

        st.progress(
            min(maior_pressao / 100, 1.0)
        )

        # ====================================================
        # ALERTAS
        # ====================================================

        if maior_pressao >= 80:

            st.error(
                f"🚨 **CHANCE QUENTE DETECTADA**\n\n"
                f"⚽ Maior pressão: {time_pressao}\n\n"
                f"📊 Índice: {maior_pressao}%"
            )

        elif maior_pressao >= 70:

            st.warning(
                f"🔥 **PRESSÃO ELEVADA**\n\n"
                f"{time_pressao} está apresentando "
                f"forte volume ofensivo.\n\n"
                f"📊 Índice: {maior_pressao}%"
            )

        elif maior_pressao >= 55:

            st.info(
                f"🟡 Pressão moderada de "
                f"{time_pressao}."
            )

        else:

            st.success(
                "🔵 Nenhuma pressão ofensiva "
                "elevada detectada."
            )

        # ====================================================
        # ESTATÍSTICAS
        # ====================================================

        if mostrar_estatisticas:

            st.markdown(
                "### 📊 Estatísticas"
            )

            finalizacoes = pegar_stat(
                estatisticas,
                [
                    "Total shots",
                    "Shots"
                ]
            )

            no_alvo = pegar_stat(
                estatisticas,
                [
                    "Shots on target"
                ]
            )

            escanteios = pegar_stat(
                estatisticas,
                [
                    "Corner kicks"
                ]
            )

            posse = pegar_stat(
                estatisticas,
                [
                    "Ball possession"
                ]
            )

            grandes = pegar_stat(
                estatisticas,
                [
                    "Big chances"
                ]
            )

            ataques = pegar_stat(
                estatisticas,
                [
                    "Dangerous attacks"
                ]
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "🎯 Finalizações",
                    f"{finalizacoes[0]:g} x {finalizacoes[1]:g}"
                )

                st.metric(
                    "🥅 No alvo",
                    f"{no_alvo[0]:g} x {no_alvo[1]:g}"
                )

            with c2:

                st.metric(
                    "🚩 Escanteios",
                    f"{escanteios[0]:g} x {escanteios[1]:g}"
                )

                st.metric(
                    "🔥 Grandes chances",
                    f"{grandes[0]:g} x {grandes[1]:g}"
                )

            with c3:

                st.metric(
                    "⚔️ Ataques perigosos",
                    f"{ataques[0]:g} x {ataques[1]:g}"
                )

                st.metric(
                    "🟢 Posse",
                    f"{posse[0]:g}% x {posse[1]:g}%"
                )

        # ====================================================
        # CARTÕES
        # ====================================================

        if mostrar_incidentes:

            cartoes_home, cartoes_away = contar_cartoes(
                incidentes
            )

            st.markdown(
                "### 🟨 Cartões"
            )

            st.write(
                f"🏠 {home}: **{cartoes_home}**"
            )

            st.write(
                f"✈️ {away}: **{cartoes_away}**"
            )

        # ====================================================
        # MOMENTUM
        # ====================================================

        if mostrar_momentum:

            with st.expander(
                "📈 Ver momentum"
            ):

                if momentum:

                    valores = []

                    for ponto in momentum:

                        valores.append({
                            "Minuto": ponto.get(
                                "minute",
                                0
                            ),
                            "Momentum": ponto.get(
                                "value",
                                0
                            )
                        })

                    st.line_chart(
                        valores,
                        x="Minuto",
                        y="Momentum"
                    )

                else:

                    st.info(
                        "Momentum não disponível."
                    )

        # ====================================================
        # DETALHES
        # ====================================================

        with st.expander(
            "🔎 Dados recebidos do SofaScore"
        ):

            st.write(
                f"Event ID: {event_id}"
            )

            st.write(
                f"Total de estatísticas: "
                f"{len(estatisticas)}"
            )

            st.write(
                f"Total de incidentes: "
                f"{len(incidentes)}"
            )

        st.divider()


# ============================================================
# AVISO
# ============================================================

st.caption(
    "⚠️ O índice de pressão é uma métrica experimental "
    "criada pelo Robô V2. Não representa probabilidade "
    "garantida de gol ou resultado."
)


# ============================================================
# ATUALIZAÇÃO AUTOMÁTICA
# ============================================================

if auto:

    time.sleep(intervalo)

    st.rerun()