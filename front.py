import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re


#-----TITULO PARTE FRONT

st.set_page_config(page_title="Dashboard Interativo", layout="wide", initial_sidebar_state="expanded")
st.title("📊 Análise de Violência — Curitiba")
st.caption("Carregue seus CSVs (Corporal, Doloso, Feminicidio, Latrocinio) ou um Excel 'Bases.xlsx'. Use a barra lateral para escolher a fonte e aplicar filtros.")


# Helpers

def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    def norm(col: str) -> str:
        col = str(col)
        repl = {"ã":"a","á":"a","à":"a","â":"a","ä":"a",
                "é":"e","è":"e","ê":"e","ë":"e",
                "í":"i","ì":"i","î":"i","ï":"i",
                "ó":"o","ò":"o","ô":"o","ö":"o",
                "ú":"u","ù":"u","û":"u","ü":"u",
                "ç":"c"}
        for k, v in repl.items(): col = col.replace(k, v)
        col = col.strip().lower()
        col = re.sub(r"[^0-9a-z_ ]", "_", col)
        col = re.sub(r"\s+", "_", col)
        col = re.sub(r"_+", "_", col).strip("_")
        return col
    df = df.copy()
    df.columns = [norm(c) for c in df.columns]
    return df

@st.cache_data(show_spinner=False)
def read_csv_smart(path: Path) -> pd.DataFrame:
    
    seps = [",", ";", "\t", "|"]
    encs = ["utf-8", "latin-1"]
    last_err = None
    for enc in encs:
        for sep in seps:
            try:
                df = pd.read_csv(path, sep=sep, encoding=enc, engine="python")
                
                if df.shape[1] == 1 and sep != ",":
                    continue
                return df
            except Exception as e:
                last_err = e
                continue
    raise RuntimeError(f"Falha ao ler '{path.name}'. Último erro: {last_err}")

@st.cache_data(show_spinner=False)
def read_excel_sheets(path: Path):
    with pd.ExcelFile(path) as xls:
        sheets = xls.sheet_names
    return sheets

@st.cache_data(show_spinner=False)
def load_excel_sheet(path: Path, sheet: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet)

def list_found_csvs(data_dir: Path):
    wanted = {"corporal.csv","doloso.csv","feminicidio.csv","latrocinio.csv"}
    found = {}
    for p in data_dir.rglob("*.csv"):
        name = p.name.casefold()
        if name in wanted and name not in found:
            found[name] = p
    return found


#----Fonte de dados (sidebar)

base_dir = Path(__file__).parent
st.sidebar.write("### 📁 Fonte dos Dados")
data_dir_input = st.sidebar.text_input("Pasta dos dados", value=str(base_dir))
data_dir = Path(data_dir_input).expanduser()

excel_path = data_dir / "Bases.xlsx"
found_excels = excel_path.exists()

found_csvs = list_found_csvs(data_dir)
csv_options = { "Homicídio Corporal":"corporal.csv",
                "Homicídio Doloso":"doloso.csv",
                "Feminicídio":"feminicidio.csv",
                "Latrocínio":"latrocinio.csv" }

mode = "CSVs" if found_csvs else ("Excel" if found_excels else "Upload")
mode = st.sidebar.radio("Selecione a fonte:", options=["CSVs","Excel","Upload"], index=["CSVs","Excel","Upload"].index(mode))


# Carregamento conforme a fonte

df = None
dataset_label = None

if mode == "CSVs":
    #---permite escolher só entre os que foram encontrados
    available_labels = [lbl for lbl, fname in csv_options.items() if fname in found_csvs]
    if not available_labels:
        st.error("❌ Não encontrei os CSVs esperados nessa pasta. Verifique o caminho e os nomes dos arquivos (Corporal.csv, Doloso.csv, Feminicidio.csv, Latrocinio.csv).")
        st.stop()
    dataset_label = st.sidebar.selectbox("📂 Base CSV:", available_labels)
    file_path = found_csvs[csv_options[dataset_label]]
    st.sidebar.success(f"Arquivo selecionado: {file_path.name}")
    df = read_csv_smart(file_path)

elif mode == "Excel":
    if not found_excels:
        st.error(f"❌ Bases.xlsx não foi encontrado em: {excel_path.resolve()}")
        st.stop()
    sheets = read_excel_sheets(excel_path)
    if not sheets:
        st.error("❌ O arquivo Excel não possui abas.")
        st.stop()
    dataset_label = st.sidebar.selectbox("📂 Aba do Excel:", sheets)
    df = load_excel_sheet(excel_path, dataset_label)

else:
    st.sidebar.info("Envie um CSV ou Excel. Para CSV: um arquivo por vez. Para Excel: um arquivo 'Bases.xlsx'.")
    up = st.sidebar.file_uploader("Envie CSV ou Excel", type=["csv","xlsx"])
    if up is None:
        st.warning("Aguardando upload...")
        st.stop()
    if up.name.lower().endswith(".csv"):
        df = pd.read_csv(up)
        dataset_label = up.name
    else:
        xls = pd.ExcelFile(up)
        sheet = st.sidebar.selectbox("Aba:", xls.sheet_names)
        df = pd.read_excel(xls, sheet_name=sheet)
        dataset_label = f"{up.name} — {sheet}"


#----Preparação do DataFrame

df = clean_columns(df)


for c in df.columns:
    if ("data" in c) or ("date" in c):
        try:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
        except Exception:
            pass


#----Filtros (sidebar)

st.sidebar.write("### 🎛️ Filtros")

date_cols = [c for c in df.columns if str(df[c].dtype).startswith("datetime64")]
if date_cols:
    dc = date_cols[0]
    min_d = pd.to_datetime(df[dc].min())
    max_d = pd.to_datetime(df[dc].max())
    if pd.notna(min_d) and pd.notna(max_d):
        d1, d2 = st.sidebar.date_input("Período", [min_d.date(), max_d.date()])
        if isinstance(d1, list):
            d1, d2 = d1
        df = df[(df[dc] >= pd.to_datetime(d1)) & (df[dc] <= pd.to_datetime(d2))]

#----Filtros numéricos
colunas_numericas = df.select_dtypes(include=["int64", "float64","int32","float32"]).columns.tolist()
for col in colunas_numericas:
    vmin = float(pd.to_numeric(df[col], errors="coerce").min())
    vmax = float(pd.to_numeric(df[col], errors="coerce").max())
    if pd.isna(vmin) or pd.isna(vmax):
        continue
    r = st.sidebar.slider(f"📊 {col}", vmin, vmax, (vmin, vmax))
    df = df[(pd.to_numeric(df[col], errors="coerce") >= r[0]) & (pd.to_numeric(df[col], errors="coerce") <= r[1])]

#----Filtros categóricos
colunas_categoricas = df.select_dtypes(include=["object"]).columns.tolist()
for col in colunas_categoricas:
    opts = sorted([o for o in df[col].dropna().unique().tolist() if str(o).strip() != "" ], key=lambda x: str(x).lower())
    if len(opts) > 0:
        sel = st.sidebar.multiselect(f"🔹 {col}", opts, default=opts[:50] if len(opts) > 50 else opts)
        df = df[df[col].isin(sel)]


#-----Config dos gráficos (sidebar)

st.sidebar.write("### 📌 Configuração dos Gráficos")
colunas_numericas = df.select_dtypes(include=["int64", "float64","int32","float32"]).columns.tolist()

if len(colunas_numericas) == 0:
    st.warning("⚠️ Não há colunas numéricas após os filtros.")
    st.stop()


coluna_x = st.sidebar.selectbox("Eixo X:", colunas_numericas, index=0)
coluna_y = st.sidebar.selectbox("Eixo Y:", colunas_numericas, index=min(1, len(colunas_numericas)-1))
use_z = st.sidebar.checkbox("Usar coluna de intensidade (Z) no heatmap", value=(len(colunas_numericas) >= 3))
coluna_valor = None
if use_z and len(colunas_numericas) >= 3:
    coluna_valor = st.sidebar.selectbox("Coluna Z (intensidade):", [c for c in colunas_numericas if c not in [coluna_x, coluna_y]], index=0)


st.subheader("📌 Principais Métricas")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("🔹 Total de Registros", f"{len(df):,}".replace(",", "."))
with c2:
    base_col = coluna_valor or coluna_y
    try:
        avg_val = pd.to_numeric(df[base_col], errors="coerce").mean()
    except Exception:
        avg_val = float("nan")
    st.metric("🔹 Média", f"{avg_val:,.2f}".replace(",", "."))
with c3:
    try:
        max_val = pd.to_numeric(df[base_col], errors="coerce").max()
    except Exception:
        max_val = float("nan")
    st.metric("🔹 Máximo", f"{max_val:,.2f}".replace(",", "."))

#----Mapa de calor

st.subheader(f"🌡️ Mapa de Calor — {dataset_label}")
try:
    if coluna_valor is not None:
        fig_hm = px.density_heatmap(df, x=coluna_x, y=coluna_y, z=coluna_valor, nbinsx=20, nbinsy=20, color_continuous_scale="Viridis")
    else:
        fig_hm = px.density_heatmap(df, x=coluna_x, y=coluna_y, nbinsx=20, nbinsy=20, color_continuous_scale="Viridis")
    fig_hm.update_layout(xaxis_title=coluna_x, yaxis_title=coluna_y)
    st.plotly_chart(fig_hm, use_container_width=True)
except Exception as e:
    st.error(f"Erro ao gerar heatmap: {e}")


#----Gráficos adicionais

st.subheader("📈 Análises Complementares")
g1, g2 = st.columns(2)

with g1:
    try:
        df_sorted = df.dropna(subset=[coluna_x]).sort_values(by=base_col, ascending=False)
        fig_bar = px.bar(df_sorted.head(10), x=coluna_x, y=base_col, color=base_col, color_continuous_scale="Blues", title="Top 10 — Barras")
        st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico de barras: {e}")

with g2:
    try:
        df_line = df.dropna(subset=[coluna_x, base_col]).sort_values(by=coluna_x)
        fig_line = px.line(df_line, x=coluna_x, y=base_col, title="Tendência no eixo X")
        st.plotly_chart(fig_line, use_container_width=True)
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico de linha: {e}")


#----Tabela

st.subheader("📄 Dados Filtrados")
st.dataframe(df, use_container_width=True)


#----Diagnóstico rápido

with st.expander("🔍 Diagnóstico do Ambiente"):
    st.write(f"📂 Pasta configurada: `{data_dir.resolve()}`")
    try:
        items = list(Path(data_dir).glob("*"))
        st.write("Arquivos nessa pasta:", [p.name for p in items[:200]])
    except Exception as e:
        st.write(f"Erro ao listar diretório: {e}")
