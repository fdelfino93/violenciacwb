import pandas as pd
import streamlit as st
import plotly.express as px
import geopandas as gpd
import json
import os
import unicodedata

# --- Configurações da página
st.set_page_config(
    page_title="Análise de Crimes",
    layout="wide",
    page_icon="🚔"
)

st.title("🚔 Análise de Crimes por Bairro, Mês e Tipo")

# --- Função util para normalização (maiúsculas, trim, sem acento)
def normaliza_txt(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
    return s

# --- Arquivos CSV
files = {
    "Lesão Corporal": "Corporal.csv",
    "Homicídio Doloso": "Doloso.csv",
    "Feminicídio": "Feminicidio.csv",
    "Latrocínio": "Latrocinio.csv",
}

dfs = []
for crime, path in files.items():
    df = pd.read_csv(path)
    df["crime"] = crime
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

# --- Transformar meses em formato longo
ordem_meses = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
df_long = df.melt(
    id_vars=["bairro", "crime"],
    value_vars=ordem_meses,
    var_name="mês",
    value_name="casos"
)
df_long["mês"] = pd.Categorical(df_long["mês"], categories=ordem_meses, ordered=True)

# --- Filtros com opção "Todos"
st.sidebar.header("Filtros")
crime_options = ["Todos"] + sorted(df_long["crime"].unique().tolist())
crime_selected = st.sidebar.multiselect("Selecione os crimes:", options=crime_options, default=["Todos"])
if "Todos" in crime_selected:
    crimes_selecionados = df_long["crime"].unique()
else:
    crimes_selecionados = crime_selected

bairro_options = ["Todos"] + sorted(df_long["bairro"].unique().tolist())
bairro_selected = st.sidebar.multiselect("Selecione os bairros:", options=bairro_options, default=["Todos"])
if "Todos" in bairro_selected:
    bairros_selecionados = df_long["bairro"].unique()
else:
    bairros_selecionados = bairro_selected

df_filtrado = df_long[
    (df_long["crime"].isin(crimes_selecionados)) &
    (df_long["bairro"].isin(bairros_selecionados))
]

# --- Gráfico 1: comparação de crimes por mês
st.subheader("📊 Comparação de crimes por mês")
fig1 = px.line(
    df_filtrado.groupby(["mês", "crime"], as_index=False)["casos"].sum(),
    x="mês", y="casos", color="crime", markers=True
)
st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico 2: comparação de crimes por bairro
st.subheader("📊 Crimes por bairro")
fig2 = px.bar(
    df_filtrado.groupby(["bairro", "crime"], as_index=False)["casos"].sum(),
    x="bairro", y="casos", color="crime", barmode="group"
)
st.plotly_chart(fig2, use_container_width=True)

# --- Gráfico 3: heatmap bairro x mês
st.subheader("🔥 Heatmap de casos por bairro e mês")
fig3 = px.density_heatmap(
    df_filtrado,
    x="mês", y="bairro", z="casos",
    color_continuous_scale="Reds",
    facet_col="crime"
)
st.plotly_chart(fig3, use_container_width=True)

# --- Gráfico 4: mapa interativo de Curitiba
st.subheader("🗺️ Mapa interativo de crimes por bairro - Curitiba")

shapefile_path = "DIVISA_DE_BAIRROS.shp"
if os.path.isfile(shapefile_path):
    gdf = gpd.read_file(shapefile_path)

    # Garantir CRS WGS84 (EPSG:4326) para Mapbox
    # - se não tiver CRS, define; se tiver diferente, reprojeta
    try:
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
    except Exception:
        # fallback em casos raros
        gdf = gdf.set_crs(epsg=4326, allow_override=True)

    # Descobrir coluna do nome do bairro
    col_bairro = None
    for candidate in ["NOME", "BAIRRO", "NOME_BAIRRO", "NM_BAIRRO", "NM_BAIR", "NOMEBAIRR"]:
        if candidate in gdf.columns:
            col_bairro = candidate
            break
    if col_bairro is None:
        col_bairro = gdf.columns  # fallback

    # Normalização de texto
    gdf[col_bairro] = gdf[col_bairro].apply(normaliza_txt)

    # Filtrar Curitiba somente se fizer sentido
    if "MUNICIPIO" in gdf.columns:
        gdf["MUNICIPIO_norm"] = gdf["MUNICIPIO"].apply(normaliza_txt)
        if (gdf["MUNICIPIO_norm"] == "CURITIBA").any():
            gdf = gdf[gdf["MUNICIPIO_norm"] == "CURITIBA"].copy()

    # Preparar dados agregados para o mapa
    df_mapa = df_filtrado.groupby("bairro", as_index=False)["casos"].sum().copy()
    df_mapa["bairro_norm"] = df_mapa["bairro"].apply(normaliza_txt)

    # Criar chave normalizada no gdf
    gdf["bairro_norm"] = gdf[col_bairro].apply(normaliza_txt)

    # Merge por chave normalizada; manter a coluna original para hover
    gdf_merged = gdf.merge(df_mapa[["bairro_norm", "casos"]], on="bairro_norm", how="left")
    gdf_merged["casos"] = gdf_merged["casos"].fillna(0)

    # Converter para GeoJSON
    geojson_bairros = json.loads(gdf_merged.to_json())

    # Importante: locations deve casar com featureidkey
    fig_map = px.choropleth_mapbox(
        gdf_merged,
        geojson=geojson_bairros,
        locations=col_bairro,  # mesma coluna existente nas properties do GeoJSON
        featureidkey=f"properties.{col_bairro}",
        color="casos",
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": -25.4284, "lon": -49.2733},
        opacity=0.6,
        hover_name=col_bairro,
        hover_data={"casos": True}
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.error(f"Arquivo Shapefile não encontrado: {shapefile_path}")
