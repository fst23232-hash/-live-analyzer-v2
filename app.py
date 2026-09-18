import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Robô V2 - Análise de Futebol",
    page_icon="⚽",
    layout="wide",
)

API_DEFAULT = "https://www.thesportsdb.com/api/v1/json/3"

st.title("⚽ Robô V2 — Análise de Jogos ao Vivo")
st.caption("Sistema de análise estatística em tempo real")
st.divider()

# -----------------------------
# Configurações
# -----------------------------
st.sidebar.header("⚙️ Configurações")
api_url = st.sidebar.text_input("URL da API", value=API_DEFAULT).rstrip("/")
auto_refresh = st.sidebar.checkbox("🔄 Atualização automática", value=False)
refresh_seconds = st.sidebar.number_input(
    "Intervalo (segundos)", min_value=15, max_value=300, value=30, step=5
)

st.sidebar.info(
    "O Robô V2 analisa dados disponíveis na API e gera indicadores "
    "informativos. Ele não realiza apostas automaticamente."
)

# -----------------------------
# Funções
# -----------------------------
def get_json(endpoint, params=None):
    url = f"{api_url}/{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def carregar_jogos():
    hoje = datetime.now().strftime("%Y-%m-%d")
    dados = get_json("eventsday.php", {"d": hoje})
    return dados.get("events") or []


def numero(valor):
    try:
        return int(valor or 0)
    except (TypeError, ValueError):
        return 0


def analisar_jogo(jogo):
    casa = numero(jogo.get("intHomeScore"))
    fora = numero(jogo.get("intAwayScore"))

    total = casa + fora
    diferenca = abs(casa - fora)

    sinais = []
    if total >= 2:
        sinais.append("Jogo com 2+ gols")
    if casa > 0 and fora > 0:
        sinais.append("Ambas marcaram")
    if diferenca >= 2:
        sinais.append("Diferença de 2+ gols")
    if total == 0:
        sinais.append("Sem gols registrados")

    # Índice informativo, sem transformar o resultado em recomendação de aposta.
    indice = 50
    indice += min(total * 8, 24)
    indice += min(diferenca * 4, 12)
    if casa > 0 and fora > 0:
        indice += 10
    indice = max(0, min(100, indice))

    return {
        "total_gols": total,
        "diferenca": diferenca,
        "indice": indice,
        "sinais": sinais,
    }


def nome_jogo(jogo):
    return (
        f"{jogo.get('strHomeTeam', 'Mandante')} × "
        f"{jogo.get('strAwayTeam', 'Visitante')}"
    )


# -----------------------------
# Estado da aplicação
# -----------------------------
if "jogos" not in st.session_state:
    st.session_state.jogos = []

if "ultima_atualizacao" not in st.session_state:
    st.session_state.ultima_atualizacao = None


# -----------------------------
# Jogos
# -----------------------------
st.subheader("🔴 Jogos do dia")

col_btn, col_status = st.columns([1, 3])

with col_btn:
    atualizar = st.button("🔄 Atualizar jogos", use_container_width=True)

if atualizar or not st.session_state.jogos:
    try:
        st.session_state.jogos = carregar_jogos()
        st.session_state.ultima_atualizacao = datetime.now()
    except requests.RequestException as erro:
        st.error(f"Erro ao consultar a API: {erro}")
    except Exception as erro:
        st.error(f"Erro inesperado: {erro}")

with col_status:
    if st.session_state.ultima_atualizacao:
        st.caption(
            "Última atualização: "
            + st.session_state.ultima_atualizacao.strftime("%d/%m/%Y %H:%M:%S")
        )

jogos = st.session_state.jogos

if not jogos:
    st.warning("Nenhum jogo encontrado para hoje.")
else:
    st.success(f"{len(jogos)} jogo(s) encontrado(s).")

    opcoes = [nome_jogo(jogo) for jogo in jogos]
    selecionado = st.selectbox("🎯 Selecione um jogo para analisar", opcoes)
    jogo = jogos[opcoes.index(selecionado)]

    casa = jogo.get("strHomeTeam", "Mandante")
    fora = jogo.get("strAwayTeam", "Visitante")
    placar_casa = numero(jogo.get("intHomeScore"))
    placar_fora = numero(jogo.get("intAwayScore"))
    status = jogo.get("strStatus") or jogo.get("strProgress") or "Não informado"

    st.divider()
    st.subheader("📌 Jogo selecionado")

    c1, c2, c3 = st.columns([3, 1, 3])
    with c1:
        st.markdown(f"### 🏠 {casa}")
    with c2:
        st.markdown(f"## {placar_casa} × {placar_fora}")
        st.caption(status)
    with c3:
        st.markdown(f"### ✈️ {fora}")

    analise = analisar_jogo(jogo)

    st.divider()
    st.subheader("📊 Indicadores")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Gols registrados", analise["total_gols"])
    with m2:
        st.metric("Diferença", analise["diferenca"])
    with m3:
        st.metric("Índice informativo", f"{analise['indice']}/100")
    with m4:
        st.metric("Sinais", len(analise["sinais"]))

    st.progress(analise["indice"] / 100)

    st.subheader("🔎 Leitura automática")
    for sinal in analise["sinais"]:
        st.write(f"• {sinal}")

    if not analise["sinais"]:
        st.info("Ainda não há dados suficientes para gerar sinais.")

    with st.expander("🧾 Dados recebidos da API"):
        st.json(jogo)

# -----------------------------
# Resumo
# -----------------------------
st.divider()
st.subheader("📈 Resumo da sessão")

jogos_analisados = len(jogos)
sinais_total = sum(len(analisar_jogo(j)["sinais"]) for j in jogos)

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Jogos carregados", jogos_analisados)
with r2:
    st.metric("Sinais encontrados", sinais_total)
with r3:
    st.metric(
        "Atualização",
        "Automática" if auto_refresh else "Manual",
    )

st.caption("Robô V2 — módulo de análise informativa.")
