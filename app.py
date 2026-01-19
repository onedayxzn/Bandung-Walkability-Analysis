import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(page_title="Bandung Walkability Dashboard", layout="wide", page_icon="🚶")

# styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #737374;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #737374;
    </style>
    """, unsafe_allow_html=True)

st.title("Bandung Urban Planning: Walkability Analysis")
st.markdown("Dashboard interaktif untuk menganalisis skor walkability per wilayah di Kota Bandung.")

@st.cache_data
def load_data():
    gdf = gpd.read_file("output/walkability_kelurahan.geojson")
    return gdf

try:
    data = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}. Pastikan Anda telah menjalankan `walkbility.py` terlebih dahulu.")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filter Wilayah")
kecamatan_list = sorted(data['kecamatan'].unique().tolist())
if "Bandung Outside" in kecamatan_list:
    kecamatan_list.remove("Bandung Outside")

selected_kec = st.sidebar.selectbox("Pilih Kecamatan", ["Semua"] + kecamatan_list)

if selected_kec != "Semua":
    filtered_data = data[data['kecamatan'] == selected_kec]
    kelurahan_list = sorted(filtered_data['kelurahan'].unique().tolist())
    selected_kel = st.sidebar.selectbox("Pilih Kelurahan", ["Semua"] + kelurahan_list)
else:
    selected_kel = "Semua"
    filtered_data = data

if selected_kel != "Semua":
    filtered_data = filtered_data[filtered_data['kelurahan'] == selected_kel]

# Metrics
col1, col2, col3, col4 = st.columns(4)
avg_score = filtered_data['score'].mean()
avg_sidewalk = filtered_data['sidewalk_pct'].mean()
avg_int = filtered_data['intersection_density'].mean()
avg_amenity = filtered_data['amenity_pct'].mean()

col1.metric("Avg Walkability", f"{avg_score:.1f}/100")
col2.metric("Avg Trotoar", f"{avg_sidewalk:.1f}%")
col3.metric("Kepadatan Persimpangan", f"{avg_int:.1f}")
col4.metric("Akses Fasilitas", f"{avg_amenity:.1f}%")

# Main Content - Full Width Map
st.subheader("Peta Skor Walkability")
# Determine center
center = [filtered_data.geometry.centroid.y.mean(), filtered_data.geometry.centroid.x.mean()]

m = folium.Map(location=center, zoom_start=14 if selected_kec != "Semua" else 12, tiles="cartodbpositron")

folium.Choropleth(
    geo_data=filtered_data,
    name="Walkability Score",
    data=filtered_data,
    columns=["kelurahan", "score"],
    key_on="feature.properties.kelurahan",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Skor Walkability (0-100)"
).add_to(m)

# Add Tooltips manually for better control
folium.features.GeoJson(
    filtered_data,
    style_function=lambda x: {'fillColor': 'transparent', 'color':'gray', 'weight':0.5},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['kecamatan', 'kelurahan', 'score', 'sidewalk_pct', 'amenity_pct'],
        aliases=['Kecamatan', 'Kelurahan', 'Skor', '% Trotoar', '% Fasilitas']
    )
).add_to(m)

# Use use_container_width=True for full width
st_folium(m, use_container_width=True, height=600, returned_objects=[])

# Charts and Tables below map
st.markdown("---")
g_col1, g_col2 = st.columns([1, 1])

with g_col1:
    st.subheader("Distribusi Skor")
    fig = px.histogram(filtered_data, x="score", nbins=20, 
                       labels={'score': 'Walkability Score'},
                       color_discrete_sequence=['#4ade80'])
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with g_col2:
    st.subheader("Top Low Walkability Areas")
    low_areas = filtered_data.sort_values(by='score').head(10)[['kecamatan', 'kelurahan', 'score']]
    st.table(low_areas)

# Data Explorer
with st.expander("Lihat Data Mentah"):
    st.dataframe(filtered_data.drop(columns='geometry'))
