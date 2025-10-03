import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Insights de Clientes", page_icon="📊", layout="wide")

# Título do app
st.title("📈 Insights de Clientes - Análise de Atividade e Riscos")
st.markdown("---")


# Função para carregar dados (com cache e tratamento de erros)
@st.cache_data
def carregar_dados(arquivo_path=None):
    df = pd.DataFrame()
    try:
        if arquivo_path is not None:
            # Se veio de uploader
            df = pd.read_excel(arquivo_path)
        else:
            # Tenta carregar de arquivo fixo
            df = pd.read_excel("Arquivo_Formatado.xlsx")

        # Reconverter "Ultima Entrega" para datetime (se foi salva como string)
        if "Ultima Entrega" in df.columns:
            df["Ultima Entrega"] = pd.to_datetime(df["Ultima Entrega"], format="%d/%m/%Y", errors="coerce")

        # Garantir que "Ativo" seja string maiúscula para consistência
        if "Ativo" in df.columns:
            df["Ativo"] = df["Ativo"].astype(str).str.upper()

        # Calcular semanas sem compra dinamicamente (baseado em Ultima Entrega)
        if "Ultima Entrega" in df.columns:
            data_atual = datetime.now()
            df["dias_sem_compra"] = (data_atual - df["Ultima Entrega"]).dt.days
            df["semanas_sem_compra"] = df["dias_sem_compra"] // 7
            df["semanas_sem_compra"] = df["semanas_sem_compra"].fillna(0).astype(int)

        return df
    except FileNotFoundError:
        st.error("Arquivo 'Arquivo_Formatado.xlsx' não encontrado. Use o uploader abaixo para carregar os dados.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}. Verifique o formato do Excel.")
        return pd.DataFrame()


# Carregamento principal: Tenta arquivo fixo ou uploader
df = pd.DataFrame()
uploaded_file = st.file_uploader("Faça upload do Arquivo_Formatado.xlsx (se o arquivo fixo não estiver disponível)",
                                 type="xlsx")

if uploaded_file is not None:
    with st.spinner("Carregando dados do upload..."):
        df = carregar_dados(uploaded_file)
else:
    with st.spinner("Carregando dados do arquivo local..."):
        df = carregar_dados()

if df.empty:
    st.stop()  # Para o app se não carregar dados

# Exibir amostra dos dados (para debug, em expander)
with st.expander("👀 Visualizar Amostra dos Dados (primeiras 5 linhas)"):
    st.dataframe(df.head(), use_container_width=True)

# Cálculos dos Insights
total_clientes = len(df)

# 1 e 2: Ativos e Inativos (baseado em coluna "Ativo")
if "Ativo" in df.columns:
    clientes_ativos = len(df[df["Ativo"] == "SIM"])
    clientes_inativos = total_clientes - clientes_ativos
else:
    st.warning("Coluna 'Ativo' não encontrada. Considerando todos como ativos para cálculos.")
    clientes_ativos = total_clientes
    clientes_inativos = 0

# 3: Compraram na última semana (baseado em Ultima Entrega)
clientes_ultima_semana = 0
if "Ultima Entrega" in df.columns:
    data_atual = datetime.now()
    data_semana_passada = data_atual - timedelta(days=7)
    clientes_ultima_semana = len(df[df["Ultima Entrega"] >= data_semana_passada].dropna(subset=["Ultima Entrega"]))

# 4: Clientes em risco (prestes a 5 semanas sem comprar) - 3 a 4 semanas sem atividade
clientes_risco = pd.DataFrame()
if "semanas_sem_compra" in df.columns:
    # Filtro: 3 a 4 semanas (próximos de 5, risco iminente)
    clientes_risco = df[(df["semanas_sem_compra"] >= 3) & (df["semanas_sem_compra"] < 5)].copy()
    # Se quiser usar coluna "Semanas" diretamente (descomente abaixo e comente o cálculo dinâmico acima)
    # clientes_risco = df[df["Semanas"] == 4].copy()  # Ajuste o valor conforme sua lógica

    # Selecionar colunas relevantes para exibição
    cols_risco = ["Cliente", "Razão Social", "semanas_sem_compra", "Ultima Entrega", "Ativo", "Total Faturado",
                  "Seguimento"]
    if "semanas_sem_compra" not in cols_risco:  # Fallback se não calculado
        cols_risco = [col for col in cols_risco if col != "semanas_sem_compra"] + ["Semanas"]
    clientes_risco = clientes_risco[[col for col in cols_risco if col in clientes_risco.columns]].sort_values(
        "semanas_sem_compra", ascending=False)

    # Formatar Ultima Entrega de volta para string legível na tabela
    if "Ultima Entrega" in clientes_risco.columns:
        clientes_risco["Ultima Entrega"] = clientes_risco["Ultima Entrega"].dt.strftime("%d/%m/%Y")
else:
    st.warning("Coluna 'Ultima Entrega' não encontrada. Não é possível calcular semanas sem compra.")

num_risco = len(clientes_risco)

# Layout das Métricas (em colunas)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Clientes", total_clientes)
    st.metric("Clientes Ativos", clientes_ativos,
              delta=f"({clientes_ativos / total_clientes:.1%} do total)" if total_clientes > 0 else "0%")

with col2:
    st.metric("Clientes Inativos", clientes_inativos, delta_color="inverse")

with col3:
    st.metric("Compraram na Última Semana", clientes_ultima_semana, delta=f"de {total_clientes} totais")

with col4:
    st.metric("Clientes em Risco (próximos de 5 semanas)", num_risco,
              delta_color="warning" if num_risco > 0 else "normal")

# Seção para lista de clientes em risco
st.markdown("---")
st.subheader("🔴 Clientes em Risco de Perda (Prestes a 5 Semanas sem Comprar)")
st.markdown(
    "*Clientes com 3-4 semanas sem atividade (risco iminente de perda). Ajuste o filtro no código se necessário.*")

if not clientes_risco.empty:
    st.dataframe(clientes_risco, use_container_width=True, hide_index=True)
    # Botão para exportar
    csv = clientes_risco.to_csv(index=False, encoding='utf-8').encode('utf-8')
    st.download_button(
        label="📥 Baixar Lista em CSV",
        data=csv,
        file_name="clientes_em_risco.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhum cliente identificado como em risco no momento. Ótimo!")

# Sidebar para mais detalhes (opcional)
with st.sidebar:
    st.header("Filtros Adicionais")
    if "Estado" in df.columns and not df.empty:
        estados = sorted(df["Estado"].unique())
        estado_filtro = st.multiselect("Filtrar por Estado", options=estados, default=estados)
        if len(estado_filtro) < len(estados):
            df_filtrado = df[df["Estado"].isin(estado_filtro)]
            st.success(f"Clientes filtrados: {len(df_filtrado)} de {total_clientes}")
            # Atualizar métricas filtradas (exemplo simples)
            if "Ativo" in df_filtrado.columns:
                st.metric("Ativos Filtrados", len(df_filtrado[df_filtrado["Ativo"] == "SIM"]))
    st.markdown("---")
    st.info("💡 Dicas:\n- Atualize o app após upload.\n- Verifique colunas: Ativo, Ultima Entrega, Semanas.")

# Rodapé
st.markdown("---")
st.caption("App desenvolvido com Streamlit e Pandas. Dados carregados de 'Arquivo_Formatado.xlsx' ou upload.")
