import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Insights de Clientes", page_icon="📊", layout="wide")

# Título do app
st.title("📈 Insights de Clientes - Análise de Atividade e Riscos")
st.markdown("---")

# Carregar o DataFrame formatado
@st.cache_data  # Cache para performance
def carregar_dados():
    try:
        df = pd.read_excel("Arquivo_Formatado.xlsx")
        # Reconverter "Ultima Entrega" para datetime (pois foi salva como string)
        if "Ultima Entrega" in df.columns:
            df["Ultima Entrega"] = pd.to_datetime(df["Ultima Entrega"], format="%d/%m/%Y", errors="coerce")
        # Garantir que "Ativo" seja string maiúscula para consistência
        if "Ativo" in df.columns:
            df["Ativo"] = df["Ativo"].astype(str).str.upper()
        return df
    except FileNotFoundError:
        st.error("Arquivo 'Arquivo_Formatado.xlsx' não encontrado. Execute o código de formatação primeiro!")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.stop()  # Para o app se não carregar dados

# Cálculos dos Insights
total_clientes = len(df)

# 1 e 2: Ativos e Inativos
clientes_ativos = len(df[df["Ativo"] == "SIM"]) if "Ativo" in df.columns else 0
clientes_inativos = total_clientes - clientes_ativos

# 3: Compraram na última semana
data_atual = datetime.now()
data_semana_passada = data_atual - timedelta(days=7)
if "Ultima Entrega" in df.columns:
    clientes_ultima_semana = len(df[df["Ultima Entrega"] >= data_semana_passada].dropna(subset=["Ultima Entrega"]))
else:
    clientes_ultima_semana = 0

# 4: Clientes em risco (prestes a 5 semanas sem comprar) - filtro em "Semanas" == 4
if "Semanas" in df.columns:
    clientes_risco = df[df["Semanas"] == 4].copy()  # Ajuste o filtro se necessário (ex: df[(df["Semanas"] >= 3) & (df["Semanas"] < 5)])
    # Selecionar colunas relevantes para exibição
    cols_risco = ["Cliente", "Razão Social", "Semanas", "Ultima Entrega", "Ativo", "Total Faturado", "Seguimento"]
    clientes_risco = clientes_risco[cols_risco].sort_values("Semanas", ascending=False)
else:
    clientes_risco = pd.DataFrame()
    st.warning("Coluna 'Semanas' não encontrada. Ajuste o código de formatação se necessário.")

# Layout das Métricas (em colunas)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Clientes", total_clientes)
    st.metric("Clientes Ativos", clientes_ativos, delta=f"({clientes_ativos / total_clientes:.1%} do total)")

with col2:
    st.metric("Clientes Inativos", clientes_inativos, delta_color="inverse")

with col3:
    st.metric("Compraram na Última Semana", clientes_ultima_semana, delta=f"de {total_clientes} totais")

with col4:
    num_risco = len(clientes_risco)
    st.metric("Clientes em Risco (próximos de 5 semanas)", num_risco, delta_color="warning" if num_risco > 0 else "normal")

# Seção para lista de clientes em risco
st.markdown("---")
st.subheader("🔴 Clientes em Risco de Perda (Prestes a 5 Semanas sem Comprar)")
st.markdown("*Clientes com exatamente 4 semanas sem atividade (ajuste o filtro no código se necessário).*")

if not clientes_risco.empty:
    st.dataframe(clientes_risco, use_container_width=True, hide_index=True)
    # Botão para exportar
    csv = clientes_risco.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Lista em CSV",
        data=csv,
        file_name="clientes_em_risco.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhum cliente identificado como em risco no momento.")

# Sidebar para mais detalhes (opcional)
with st.sidebar:
    st.header("Filtros Adicionais")
    if "Estado" in df.columns:
        estados = df["Estado"].unique()
        estado_filtro = st.multiselect("Filtrar por Estado", options=estados, default=estados)
        if estado_filtro:
            df_filtrado = df[df["Estado"].isin(estado_filtro)]
            st.write(f"Clientes filtrados: {len(df_filtrado)}")
    st.markdown("---")
    st.info("Atualize o app se alterar os dados.")

# Rodapé
st.markdown("---")
st.caption("App desenvolvido com Streamlit e Pandas. Dados carregados de 'Arquivo_Formatado.xlsx'.")
