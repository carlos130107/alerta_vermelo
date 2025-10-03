import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Insights de Clientes", page_icon="📊", layout="wide")

# Título
st.title("📈 Insights de Clientes - Análise de Atividade e Riscos")
st.markdown("---")

# Função para carregar dados (com cache)
@st.cache_data
def carregar_dados(arquivo_path=None):
    try:
        if arquivo_path is not None:
            df = pd.read_excel(arquivo_path)
        else:
            df = pd.read_excel("Arquivo_Formatado.xlsx")

        # Garantir consistência em "Ativo" (maiúscula)
        if "Ativo" in df.columns:
            df["Ativo"] = df["Ativo"].astype(str).str.upper()

        # Converter "Semanas" para int se for string
        if "Semanas" in df.columns:
            df["Semanas"] = pd.to_numeric(df["Semanas"], errors='coerce').fillna(0).astype(int)

        return df
    except FileNotFoundError:
        st.error("Arquivo 'Arquivo_Formatado.xlsx' não encontrado. Use o uploader.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar: {str(e)}")
        return pd.DataFrame()

# Carregamento
uploaded_file = st.file_uploader("Upload do Arquivo_Formatado.xlsx", type="xlsx")
df = carregar_dados(uploaded_file) if uploaded_file else carregar_dados()

if df.empty:
    st.stop()

# Sidebar para Filtros Hierárquicos (Gerente > Supervisor > Vendedor)
st.sidebar.header("🔍 Filtros por Equipe")
df_filtrado = df.copy()  # Começa com toda a base

# Verificar colunas de filtro
if all(col in df.columns for col in ["Gerente", "Supervisor", "Vendedor"]):
    # Opções para Gerente (todos únicos, incluindo NaN como "Não Atribuído")
    gerentes = sorted(df["Gerente"].dropna().unique().tolist() + ["Não Atribuído"])
    gerente_sel = st.sidebar.multiselect("Selecione Gerente(s)", options=gerentes, default=[])

    # Filtrar por Gerente
    if gerente_sel:
        if "Não Atribuído" in gerente_sel:
            df_temp = df[df["Gerente"].isna() | df["Gerente"].isin([g for g in gerente_sel if g != "Não Atribuído"])]
        else:
            df_temp = df[df["Gerente"].isin(gerente_sel)]
        df_filtrado = df_temp
        st.sidebar.info(f"Filtrado por {len(gerente_sel)} gerente(s)")
    else:
        df_temp = df
        st.sidebar.info("Nenhum filtro de gerente aplicado")

    # Opções para Supervisor (cascata: só dos gerentes filtrados)
    if len(df_filtrado) > 0:
        supervisores = sorted(df_filtrado["Supervisor"].dropna().unique().tolist() + ["Não Atribuído"])
        supervisor_sel = st.sidebar.multiselect("Selecione Supervisor(es)", options=supervisores, default=[])

        # Filtrar por Supervisor
        if supervisor_sel:
            if "Não Atribuído" in supervisor_sel:
                df_temp2 = df_filtrado[df_filtrado["Supervisor"].isna() | df_filtrado["Supervisor"].isin([s for s in supervisor_sel if s != "Não Atribuído"])]
            else:
                df_temp2 = df_filtrado[df_filtrado["Supervisor"].isin(supervisor_sel)]
            df_filtrado = df_temp2
            st.sidebar.info(f"Filtrado por {len(supervisor_sel)} supervisor(es)")
        else:
            df_temp2 = df_filtrado
            st.sidebar.info("Nenhum filtro de supervisor aplicado")

        # Opções para Vendedor (cascata: só dos supervisores filtrados)
        if len(df_filtrado) > 0:
            vendedores = sorted(df_filtrado["Vendedor"].dropna().unique().tolist() + ["Não Atribuído"])
            vendedor_sel = st.sidebar.multiselect("Selecione Vendedor(es)", options=vendedores, default=[])

            # Filtrar por Vendedor
            if vendedor_sel:
                if "Não Atribuído" in vendedor_sel:
                    df_filtrado = df_filtrado[df_filtrado["Vendedor"].isna() | df_filtrado["Vendedor"].isin([v for v in vendedor_sel if v != "Não Atribuído"])]
                else:
                    df_filtrado = df_filtrado[df_filtrado["Vendedor"].isin(vendedor_sel)]
                st.sidebar.info(f"Filtrado por {len(vendedor_sel)} vendedor(es)")
            else:
                st.sidebar.info("Nenhum filtro de vendedor aplicado")
    else:
        st.sidebar.warning("Nenhum cliente após filtro de gerente.")

    # Métrica de resumo na sidebar
    total_filtrado = len(df_filtrado)
    st.sidebar.metric("Clientes Filtrados", total_filtrado, delta=f"{total_filtrado / len(df):.1%} do total" if len(df) > 0 else "0%")
else:
    st.sidebar.warning("Colunas 'Gerente', 'Supervisor' ou 'Vendedor' não encontradas. Filtros desabilitados.")
    df_filtrado = df

# Cálculos (agora baseados em df_filtrado)
total_clientes = len(df_filtrado)

# 1 e 2: Ativos e Inativos
if "Ativo" in df_filtrado.columns:
    clientes_ativos = len(df_filtrado[df_filtrado["Ativo"] == "SIM"])
    clientes_inativos = len(df_filtrado[df_filtrado["Ativo"] == "NÃO"])
else:
    st.warning("Coluna 'Ativo' não encontrada.")
    clientes_ativos = clientes_inativos = 0

# 3: Compraram na última semana ("Semanas" == 0)
clientes_ultima_semana = len(df_filtrado[df_filtrado["Semanas"] == 0]) if "Semanas" in df_filtrado.columns else 0

# 4: Clientes em risco ("Semanas" == 4, prestes a 5 semanas)
clientes_risco = pd.DataFrame()
if "Semanas" in df_filtrado.columns:
    clientes_risco = df_filtrado[df_filtrado["Semanas"] == 4].copy()
    # Colunas para exibição (adicionadas: telefone, cpf, cnpj; ordem lógica)
    cols_risco = ["Cliente", "Razão Social", "Telefone", "CPF / CNPJ", "Semanas", "Ativo"]
    clientes_risco = clientes_risco[[col for col in cols_risco if col in clientes_risco.columns]]
    clientes_risco = clientes_risco.sort_values("Semanas", ascending=False)
num_risco = len(clientes_risco)

if "Semanas" not in df_filtrado.columns:
    st.warning("Coluna 'Semanas' não encontrada. Cálculos de semanas desabilitados.")

# Layout das Métricas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Clientes", total_clientes)

with col2:
    st.metric("Clientes Ativos", clientes_ativos,
              delta=f"{clientes_ativos / total_clientes:.1%}" if total_clientes > 0 else "0%")

with col3:
    st.metric("Clientes Inativos", clientes_inativos,
              delta=f"{clientes_inativos / total_clientes:.1%}" if total_clientes > 0 else "0%")

with col4:
    st.metric("Compraram na Última Semana", clientes_ultima_semana)

# Métrica extra para risco (sem delta_color, pois não há delta)
st.metric("Clientes em Risco (4 semanas sem comprar)", num_risco)

# Tabela de Clientes em Risco
st.markdown("---")
st.subheader("🔴 Clientes prestes a ficar 5 semanas sem comprar (Risco de Perda)")
if not clientes_risco.empty:
    st.dataframe(clientes_risco, use_container_width=True, hide_index=True)
    # Download CSV (inclui as novas colunas)
    csv = clientes_risco.to_csv(index=False, encoding='utf-8').encode('utf-8')
    st.download_button("📥 Baixar Lista em CSV", csv, "clientes_em_risco.csv", "text/csv")
else:
    st.info("Nenhum cliente em risco identificado.")

# Rodapé
st.markdown("---")
st.caption("App com Streamlit e Pandas. Verifique colunas: Cliente, Ativo, Semanas, Telefone, CPF / CNPJ, Gerente, Supervisor, Vendedor.")
