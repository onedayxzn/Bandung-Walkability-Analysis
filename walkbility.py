# walkability.py
import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from shapely.geometry import Point, LineString, Polygon
from tqdm import tqdm

ox.settings.use_cache = True
ox.settings.log_console = False
ox.settings.timeout = 180

# ---------------------------
# Konfigurasi
# ---------------------------
WALK_BUFFER_M = 400
GRID_SIZE_M = 500  # Meningkatkan resolusi untuk cakupan administrasi lebih baik

def graph_to_gdfs(G):
    nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
    return nodes, edges

def add_node_degree(G, nodes_gdf):
    deg_dict = dict(G.degree())
    nodes_gdf["degree"] = nodes_gdf.index.map(lambda nid: deg_dict.get(nid, 0))
    return nodes_gdf

def create_grid(boundary_gdf, size_m):
    # Proyeksikan ke 3857 agar grid dalam satuan meter
    boundary_3857 = boundary_gdf.to_crs(epsg=3857)
    minx, miny, maxx, maxy = boundary_3857.total_bounds
    
    cols = list(np.arange(minx, maxx + size_m, size_m))
    rows = list(np.arange(miny, maxy + size_m, size_m))
    
    polygons = []
    for x in cols[:-1]:
        for y in rows[:-1]:
            polygons.append(Polygon([(x, y), (x + size_m, y), (x + size_m, y + size_m), (x, y + size_m)]))
            
    grid = gpd.GeoDataFrame({"geometry": polygons}, crs="EPSG:3857")
    # Filter grid yang bersinggungan dengan batas kota
    grid = grid[grid.intersects(boundary_3857.unary_union)].copy()
    grid["grid_id"] = range(len(grid))
    return grid

def calculate_metrics(local_nodes, local_edges, area_m2, amenities_gdf):
    # 1. Intersection Density (node degree >= 3)
    intersections = local_nodes[local_nodes["degree"] >= 3]
    area_km2 = area_m2 / 1e6
    int_density = len(intersections) / area_km2 if area_km2 > 0 else 0

    # 2. Avg Block Length
    if "length" not in local_edges.columns:
        local_edges["length"] = local_edges.geometry.length
    avg_block = local_edges["length"].mean() if not local_edges.empty else 0

    # 3. Sidewalk Coverage
    def has_sidewalk(row):
        s = row.get("sidewalk", "no")
        if isinstance(s, list): s = s[0]
        hw = row.get("highway", "")
        return str(s).lower() not in ["no", "0", "false", "nan", "none", "null"] or hw == "footway"

    local_edges["has_sidewalk"] = local_edges.apply(has_sidewalk, axis=1)
    total_len = local_edges["length"].sum()
    sidewalk_len = local_edges.loc[local_edges["has_sidewalk"], "length"].sum()
    sidewalk_pct = (sidewalk_len / total_len) * 100 if total_len > 0 else 0

    # 4. Amenity Accessibility
    if amenities_gdf.empty or local_nodes.empty:
        amenity_pct = 0
    else:
        # Spatial query menggunakan sindex
        sindex = amenities_gdf.sindex
        count_accessible = 0
        for pt in local_nodes.geometry:
            possible_indices = list(sindex.intersection(pt.buffer(WALK_BUFFER_M).bounds))
            possible_amenities = amenities_gdf.iloc[possible_indices]
            if not possible_amenities.empty:
                if possible_amenities.distance(pt).min() <= WALK_BUFFER_M:
                    count_accessible += 1
        amenity_pct = (count_accessible / len(local_nodes)) * 100

    return {
        "intersection_density": int_density,
        "avg_block_length": avg_block,
        "sidewalk_pct": sidewalk_pct,
        "amenity_pct": amenity_pct
    }

def normalize_metrics(m):
    # Referensi Threshold
    ranges = {
        "intersection_density": (0, 80),
        "avg_block_length": (50, 400),
        "sidewalk_pct": (0, 20),
        "amenity_pct": (0, 40)
    }
    def norm(val, r, inv=False):
        s = (val - r[0]) / (r[1] - r[0])
        if inv: s = 1 - s
        return float(np.clip(s * 100, 0, 100))

    ni = norm(m["intersection_density"], ranges["intersection_density"])
    nb = norm(m["avg_block_length"], ranges["avg_block_length"], inv=True)
    ns = norm(m["sidewalk_pct"], ranges["sidewalk_pct"])
    na = norm(m["amenity_pct"], ranges["amenity_pct"])
    
    score = (ni * 0.4) + (nb * 0.3) + (ns * 0.15) + (na * 0.15)
    return score, {"n_int": ni, "n_block": nb, "n_sidewalk": ns, "n_amenity": na}

import sys

def run_walkability(place_name, output_dir="output"):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    print(f"--- Memulai Analisis: {place_name} ---")
    sys.stdout.flush()
    
    # [1] Boundary
    boundary_gdf = ox.geocode_to_gdf(place_name)
    print(f"Boundary bounds (WGS84): {boundary_gdf.total_bounds}")
    sys.stdout.flush()
    boundary_poly = boundary_gdf.geometry.iloc[0]
    
    # [1.b] Fetch Administrative Boundaries for Filtering (Improved)
    print("Mengambil batas administrasi (Kecamatan & Kelurahan)...")
    try:
        # Fetch levels 6, 7, 8 which often contain Kecamatan/Kelurahan in Indonesia
        admin_tags = {"boundary": "administrative", "admin_level": ["6", "7", "8"]}
        all_admin = ox.features_from_polygon(boundary_poly, tags=admin_tags)
        
        # Standardize
        all_admin = all_admin[all_admin.geom_type.isin(['Polygon', 'MultiPolygon'])]
        all_admin = all_admin.to_crs(epsg=3857)
        
        # Distinguish Kecamatan and Kelurahan
        # Usually level 6 is Kecamatan, level 7 or 8 is Kelurahan in Bandung
        kec_gdf = all_admin[all_admin['admin_level'] == '6'][['name', 'geometry']].rename(columns={'name': 'kecamatan'})
        kel_gdf = all_admin[all_admin['admin_level'].isin(['7', '8'])][['name', 'geometry']].rename(columns={'name': 'kelurahan'})
        
        # Remove empty or invalid names
        kec_gdf = kec_gdf[kec_gdf['kecamatan'].notna()]
        kel_gdf = kel_gdf[kel_gdf['kelurahan'].notna()]
        
        print(f"  Berhasil memuat {len(kec_gdf)} Kecamatan dan {len(kel_gdf)} Kelurahan kandidat.")
    except Exception as e:
        print(f"  Gagal mengambil batas administrasi: {e}")
        kec_gdf = gpd.GeoDataFrame(columns=['kecamatan', 'geometry'], crs="EPSG:3857")
        kel_gdf = gpd.GeoDataFrame(columns=['kelurahan', 'geometry'], crs="EPSG:3857")

    # [2] Graph Jalan
    print("Mendownload graph jalan...")
    G = ox.graph_from_polygon(boundary_poly, network_type="walk")
    nodes, edges = graph_to_gdfs(G)
    nodes = add_node_degree(G, nodes)
    
    nodes = nodes.to_crs(epsg=3857)
    edges = edges.to_crs(epsg=3857)
    print(f"Nodes terunduh: {len(nodes)}")
    sys.stdout.flush()
    
    # [3] Amenities
    print("Mengambil data fasilitas umum...")
    sys.stdout.flush()
    tags = {"amenity": True, "shop": True, "leisure": True, "tourism": True}
    try:
        try:
            amenities = ox.features_from_polygon(boundary_poly, tags)
        except:
            amenities = ox.features_from_place(place_name, tags)
        amenities = amenities.to_crs(epsg=3857)
        amenities["geometry"] = amenities.geometry.centroid
        print(f"Fasilitas terunduh: {len(amenities)}")
    except Exception as e:
        amenities = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:3857")
        print(f"Fasilitas tidak ditemukan atau error: {e}")
    sys.stdout.flush()

    # [4] Prepare Kelurahan Polygons as Analysis Units
    print("Menyiapkan poligon Kelurahan sebagai unit analisis...")
    sys.stdout.flush()
    
    if kel_gdf.empty:
        print("ERROR: Tidak ada data Kelurahan. Analisis tidak dapat dilanjutkan.")
        return
    
    # Use Kelurahan as primary units
    analysis_units = kel_gdf.copy()
    analysis_units = analysis_units.to_crs(epsg=3857)
    
    # Add unique ID
    analysis_units['unit_id'] = range(len(analysis_units))
    
    # Add Kecamatan labels via spatial join (representative point)
    units_points = analysis_units.copy()
    units_points['geometry'] = units_points.geometry.representative_point()
    units_points['orig_index'] = units_points.index
    
    if not kec_gdf.empty:
        units_points = gpd.sjoin(units_points, kec_gdf, how="left", predicate="within")
        units_points = units_points.drop_duplicates(subset='orig_index')
        units_points = units_points.drop(columns='index_right', errors='ignore')
        analysis_units['kecamatan'] = units_points.set_index('orig_index')['kecamatan'].fillna('Unknown')
    else:
        analysis_units['kecamatan'] = 'Unknown'
    
    print(f"Total Kelurahan untuk dianalisis: {len(analysis_units)}")
    print(f"Bounds (3857): {analysis_units.total_bounds}")
    sys.stdout.flush()

    # [5] Spatial Join (Pemetaan Jalan ke Kelurahan)
    print("Memetakan jalan ke Kelurahan...")
    sys.stdout.flush()
    nodes_with_units = gpd.sjoin(nodes, analysis_units, how="inner", predicate="intersects")
    edges_with_units = gpd.sjoin(edges, analysis_units, how="inner", predicate="intersects")
    
    print(f"Hasil Join: {len(nodes_with_units)} nodes masuk ke Kelurahan.")
    sys.stdout.flush()
    
    # [6] Loop Analisis per Kelurahan
    results = []
    print("Menghitung skor per Kelurahan...")
    for idx, unit in tqdm(analysis_units.iterrows(), total=len(analysis_units)):
        uid = unit.unit_id
        
        unit_nodes = nodes_with_units[nodes_with_units.unit_id == uid].copy()
        unit_edges = edges_with_units[edges_with_units.unit_id == uid].copy()
        
        if unit_nodes.empty:
            results.append({"score": 0, "intersection_density": 0, "avg_block_length": 0, "sidewalk_pct": 0, "amenity_pct": 0, "n_int": 0, "n_block": 0, "n_sidewalk": 0, "n_amenity":0})
            continue
            
        m = calculate_metrics(unit_nodes, unit_edges, unit.geometry.area, amenities)
        score, norm_m = normalize_metrics(m)
        results.append({"score": score, **m, **norm_m})

    res_df = pd.DataFrame(results)
    analysis_units = pd.concat([analysis_units.reset_index(drop=True), res_df], axis=1)

    # [7] Simpan
    units_wgs84 = analysis_units.to_crs(epsg=4326)
    units_wgs84.to_file(f"{output_dir}/walkability_kelurahan.geojson", driver='GeoJSON')
    units_wgs84.drop(columns='geometry').to_csv(f"{output_dir}/walkability_stats.csv", index=False)

    # [8] Visualisasi (Simplified, App will do the heavy lifting)
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12, tiles="cartodbpositron")
    folium.Choropleth(
        geo_data=units_wgs84,
        name="Walkability",
        data=units_wgs84,
        columns=["kelurahan", "score"],
        key_on="feature.properties.kelurahan",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Skor Walkability (0-100)"
    ).add_to(m)
    
    m.save(f"{output_dir}/walkability_map.html")
    print(f"Analisis Selesai! Hasil di folder '{output_dir}/'")

if __name__ == "__main__":
    run_walkability("Bandung, Indonesia", output_dir="output")
