import geopandas as gpd

# supondo que o shapefile se chame bairros_curitiba.shp
gdf = gpd.read_file("bairros_curitiba.shp")
# Opcional: filtrar para ter só os atributos de bairro e geometria correta

gdf.to_file("curitiba_bairros.geojson", driver="GeoJSON")
