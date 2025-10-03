import pandas as pd

arquivo = "dados.xlsx"
df = pd.read_excel(arquivo)

# === 1. EXCLUIR COLUNAS DESNECESSÁRIAS ===
colunas_para_excluir = ["Cliente Desde", "Logradouro", "Marcar", "Inad."]
df = df.drop(columns=[col for col in colunas_para_excluir if col in df.columns])

# === 2. EXCLUIR LINHAS VAZIAS EM "Razão Social" ===
if "Razão Social" in df.columns:
    df = df.dropna(subset=["Razão Social"])
    df = df[df["Razão Social"].astype(str).str.strip() != ""]

# === 3. AJUSTAR TELEFONE ===
if "Telefone" in df.columns:
    df["Telefone"] = df["Telefone"].fillna("").astype(str)
    df["Telefone"] = df["Telefone"].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
    df["Telefone"] = df["Telefone"].replace("", "Sem Número")

# === 4. AJUSTAR CPF / CNPJ ===
if "CPF / CNPJ" in df.columns:
    df["CPF / CNPJ"] = df["CPF / CNPJ"].fillna("").astype(str)
    df["CPF / CNPJ"] = df["CPF / CNPJ"].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
    df["CPF / CNPJ"] = df["CPF / CNPJ"].replace("", "Sem Número")

# === 5. TRANSFORMAR EM MAIÚSCULAS ===
colunas_maiusculas = [
    "Razão Social", "PF/PJ", "Estado", "Cidade",
    "Nome do Gerente", "Nome do Supervisor",
    "Nome do Vendedor", "Seguimento", "Ativo"
]

for col in colunas_maiusculas:
    if col in df.columns and df[col].dtype == "object":
        df[col] = df[col].str.upper()

# === 6. AJUSTAR "Ultima Entrega" ===
if "Ultima Entrega" in df.columns:
    # Converter em datetime
    df["Ultima Entrega"] = pd.to_datetime(df["Ultima Entrega"], errors="coerce", dayfirst=True)
    # Ordenar do mais recente para o mais antigo
    df = df.sort_values(by="Ultima Entrega", ascending=False)
    # Formatar para DD/MM/YYYY
    df["Ultima Entrega"] = df["Ultima Entrega"].dt.strftime("%d/%m/%Y")

# === 7. SALVAR RESULTADO ===
df.to_excel("Arquivo_Formatado.xlsx", index=False)

print("Arquivo formatado salvo com sucesso!")
