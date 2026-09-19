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

BASE_URL = "https://www.sofascore.com/api/v1"

st.title("⚽ Robô V2 - Live Analyzer")
st.caption("Análise automática de futebol ao vivo usando dados do SofaScore")

# ============================================================
# FUNÇÕES
# ============================================================

def requisicao(url):
    try:
        resposta = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if resposta.status_code != 200:
            return {}

        return resposta.json()

    except Exception:
        return {}


def buscar_jogos_ao_vivo():
    url = f"{BASE_URL}/sport/football/events/live"

    dados = requisicao(url)

    return dados.get("events", [])


def obter_estatisticas(event_id):
    url = f"{BASE_URL}/event/{event_id}/statistics"

    dados = requisicao(url)

    return dados.get("statistics", [])


def obter_periodo_atual(event_id):
    url = f"{BASE_URL}/event/{event_id}"

    dados = requisicao(url)

    return dados.get("event", {})


def numero(valor):
    try:
        return int(valor)
    except Exception:
        return 0


def analisar_jogo(evento):
    home = evento.get("homeTeam", {})
    away = evento.get("awayTeam", {})

    nome_casa = home.get("name", "Casa")
    nome_fora = away.get("name", "Fora")

    placar_casa = numero(
        evento.get("homeScore", {}).get("current", 0)
    )

    placar_fora = numero(
        evento.get("awayScore", {}).get("current", 0)
    )

    minuto = evento.get("time", {}).get("current", 0)

    status = evento.get("status", {}).get("type", "")

    # --------------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------------

    estatisticas = obter_estatisticas(
        evento.get("id")
    )

    escanteios_casa = 0
    escanteios_fora = 0

    ataques_casa = 0
    ataques_fora = 0

    ataques_perigosos_casa = 0
    ataques_perigosos_fora = 0

    finalizacoes_casa = 0
    finalizacoes_fora = 0

    chutes_no_gol_casa = 0
    chutes_no_gol_fora = 0

    posse_casa = 0
    posse_fora = 0

    # --------------------------------------------------------
    # LEITURA DAS ESTATÍSTICAS DO SOFASCORE
    # --------------------------------------------------------

    if estatisticas:

        for periodo in estatisticas:

            grupos = periodo.get("groups", [])

            for grupo in grupos:

                itens = grupo.get("statisticsItems", [])

                for item in itens:

                    nome = str(
                        item.get("name", "")
                    ).lower()

                    casa = item.get("home")
                    fora = item.get("away")

                    casa = numero(casa)
                    fora = numero(fora)

                    if "corner" in nome or "escante" in nome:
                        escanteios_casa = casa
                        escanteios_fora = fora

                    elif "dangerous attack" in nome or "ataques perigosos" in nome:
                        ataques_perigosos_casa = casa
                        ataques_perigosos_fora = fora

                    elif "attack" in nome or "ataques" in nome:
                        ataques_casa = casa
                        ataques_fora = fora

                    elif "shots on target" in nome or "chutes no gol" in nome:
                        chutes_no_gol_casa = casa
                        chutes_no_gol_fora = fora

                    elif "shots" in nome or "finaliz" in nome:
                        finalizacoes_casa = casa
                        finalizacoes_fora = fora

                    elif "possession" in nome or "posse" in nome:
                        posse_casa = casa
                        posse_fora = fora

    # --------------------------------------------------------
    # ÍNDICE DE PRESSÃO
    # --------------------------------------------------------

    pressao_casa = (
        ataques_perigosos_casa * 2
        + chutes_no_gol_casa * 4
        + finalizacoes_casa * 1
        + escanteios_casa * 2
    )

    pressao_fora = (
        ataques_perigosos_fora * 2
        + chutes_no_gol_fora * 4
        + finalizacoes_fora * 1
        + escanteios_fora * 2
    )

    pressao_total = pressao_casa + pressao_fora

    # --------------------------------------------------------
    # NÍVEL DE PRESSÃO
    # --------------------------------------------------------

    if pressao_total >= 60:
        nivel = "🔥 MUITO ALTA"

    elif pressao_total >= 40:
        nivel = "🟠 ALTA"

    elif pressao_total >= 20:
        nivel = "🟡 MODERADA"

    else:
        nivel = "⚪ BAIXA"

    # --------------------------------------------------------
    # TIME MAIS ATIVO
    # --------------------------------------------------------

    if pressao_casa > pressao_fora:
        time_pressao = nome_casa

    elif pressao_fora > pressao_casa:
        time_pressao = nome_fora

    else:
        time_pressao = "Equilibrado"

    # --------------------------------------------------------
    # RETORNO
    # --------------------------------------------------------

    return {
        "nome_casa": nome_casa,
        "nome_fora": nome_fora,
        "placar_casa": placar_casa,
        "placar_fora": placar_fora,
        "minuto": minuto,
        "status": status,
        "escanteios_casa": escanteios_casa,
        "escanteios_fora": escanteios_fora,
        "ataques_casa": ataques_casa,
        "ataques_fora": ataques_fora,
        "ataques_perigosos_casa": ataques_perigosos_casa,
        "ataques_perigosos_fora": ataques_perigosos_fora,
        "finalizacoes_casa": finalizacoes_casa,
        "finalizacoes_fora": finalizacoes_fora,
        "chutes_no_gol_casa": chutes_no_gol_casa,
        "chutes_no_gol_fora": chutes_no_gol_fora,
        "posse_casa": posse_casa,
        "posse_fora": posse_fora,
        "pressao_casa": pressao_casa,
        "pressao_fora": pressao_fora,
        "pressao_total": pressao_total,
        "nivel": nivel,
        "time_pressao": time_pressao
    }


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Configurações")

atualizacao = st.sidebar.slider(
    "Atualização automática (segundos)",
    min_value=10,
    max_value=120,
    value=30,
    step=10
)

mostrar_baixa = st.sidebar.checkbox(
    "Mostrar jogos com pressão baixa",
    value=True
)

# ============================================================
# ATUALIZAÇÃO
# ============================================================

agora = datetime.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

st.info(
    f"🕐 Última atualização: {agora}"
)

# ============================================================
# BUSCAR JOGOS
# ============================================================

jogos = buscar_jogos_ao_vivo()

if not jogos:

    st.warning(
        "⚠️ Nenhum jogo de futebol ao vivo foi encontrado neste momento."
    )

    st.info(
        "Quando houver partidas ao vivo, elas aparecerão automaticamente aqui."
    )

else:

    st.success(
        f"⚽ {len(jogos)} jogo(s) encontrado(s) ao vivo."
    )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    resultados = []

    for jogo in jogos:

        try:

            analise = analisar_jogo(jogo)

            resultados.append(analise)

        except Exception as erro:

            st.warning(
                f"Erro ao analisar uma partida: {erro}"
            )

    # ========================================================
    # EXIBIÇÃO
    # ========================================================

    for jogo in resultados:

        if (
            not mostrar_baixa
            and jogo["nivel"] == "⚪ BAIXA"
        ):
            continue

        st.markdown("---")

        col1, col2, col3 = st.columns(
            [3, 2, 3]
        )

        with col1:

            st.subheader(
                jogo["nome_casa"]
            )

            st.metric(
                "Placar",
                jogo["placar_casa"]
            )

        with col2:

            st.markdown(
                f"### ⏱️ {jogo['minuto']}'"
            )

            st.write(
                jogo["nivel"]
            )

        with col3:

            st.subheader(
                jogo["nome_fora"]
            )

            st.metric(
                "Placar",
                jogo["placar_fora"]
            )

        # ----------------------------------------------------
        # PRESSÃO
        # ----------------------------------------------------

        st.markdown(
            "### 🔥 Índice de pressão"
        )

        p1, p2, p3 = st.columns(3)

        with p1:

            st.metric(
                jogo["nome_casa"],
                jogo["pressao_casa"]
            )

        with p2:

            st.metric(
                "Total",
                jogo["pressao_total"]
            )

        with p3:

            st.metric(
                jogo["nome_fora"],
                jogo["pressao_fora"]
            )

        st.write(
            f"🎯 Time com maior pressão: **{jogo['time_pressao']}**"
        )

        # ----------------------------------------------------
        # ESTATÍSTICAS
        # ----------------------------------------------------

        st.markdown(
            "### 📊 Estatísticas ao vivo"
        )

        e1, e2, e3, e4 = st.columns(4)

        with e1:

            st.metric(
                "🚩 Escanteios",
                f"{jogo['escanteios_casa']} x {jogo['escanteios_fora']}"
            )

        with e2:

            st.metric(
                "⚡ Ataques perigosos",
                f"{jogo['ataques_perigosos_casa']} x {jogo['ataques_perigosos_fora']}"
            )

        with e3:

            st.metric(
                "🥅 Finalizações",
                f"{jogo['finalizacoes_casa']} x {jogo['finalizacoes_fora']}"
            )

        with e4:

            st.metric(
                "🎯 Chutes no gol",
                f"{jogo['chutes_no_gol_casa']} x {jogo['chutes_no_gol_fora']}"
            )

        # ----------------------------------------------------
        # POSSE
        # ----------------------------------------------------

        st.write(
            f"⚽ Posse de bola: "
            f"**{jogo['posse_casa']}% x {jogo['posse_fora']}%**"
        )

# ============================================================
# AVISO
# ============================================================

st.markdown("---")

st.caption(
    "⚠️ O índice de pressão é uma métrica experimental criada pelo Robô V2. "
    "Ele serve para organizar dados ao vivo e não representa probabilidade "
    "garantida de resultado."
)

# ============================================================
# ATUALIZAÇÃO AUTOMÁTICA
# ============================================================

time.sleep(atualizacao)

st.rerun()