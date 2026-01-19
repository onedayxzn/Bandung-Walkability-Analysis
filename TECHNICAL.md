# Technical Documentation - Bandung Walkability Analysis

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Data Sources (OSM)                     │
│  - Road Networks  - POIs  - Admin Boundaries            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              walkbility.py (Core Engine)                 │
│  - Data Fetching    - Spatial Analysis                  │
│  - Metric Calculation  - Scoring Algorithm              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Output Files                            │
│  - walkability_kelurahan.geojson                        │
│  - walkability_stats.csv                                │
│  - walkability_map.html                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              app.py (Dashboard)                          │
│  - Data Loading  - Filtering  - Visualization           │
└─────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. walkbility.py

#### Main Functions

##### `graph_to_gdfs(G)`
Converts NetworkX graph to GeoDataFrames.
- **Input**: NetworkX MultiDiGraph
- **Output**: (nodes_gdf, edges_gdf)
- **CRS**: Preserves original CRS from graph

##### `add_node_degree(G, nodes_gdf)`
Adds degree (number of connections) to each node.
- **Input**: Graph G, nodes GeoDataFrame
- **Output**: nodes_gdf with 'degree' column
- **Use**: Identifies intersections (degree > 2)

##### `create_grid(boundary_gdf, size_m)`
**DEPRECATED** - No longer used in Kelurahan-based analysis.
Previously created rectangular grid cells.

##### `calculate_metrics(nodes, edges, area_m2, amenities)`
Calculates raw walkability metrics for a spatial unit.

**Parameters**:
- `nodes`: GeoDataFrame of road network nodes
- `edges`: GeoDataFrame of road network edges
- `area_m2`: Area of the analysis unit in m²
- `amenities`: GeoDataFrame of POI locations

**Returns**: Dictionary with keys:
- `intersection_density`: Intersections per km²
- `avg_block_length`: Average edge length in meters
- `sidewalk_pct`: Percentage of edges with sidewalk data
- `amenity_pct`: Percentage of nodes within 400m of amenity
- `n_int`, `n_block`, `n_sidewalk`, `n_amenity`: Raw counts

**Algorithm**:
```python
# Intersection density
intersections = nodes[nodes['degree'] > 2]
density = len(intersections) / (area_m2 / 1_000_000)

# Block length
avg_length = edges['length'].mean()

# Sidewalk coverage
sidewalk_edges = edges[edges['sidewalk'].notna()]
sidewalk_pct = len(sidewalk_edges) / len(edges) * 100

# Amenity access
buffered_amenities = amenities.buffer(400)
nodes_with_access = nodes[nodes.intersects(buffered_amenities.unary_union)]
amenity_pct = len(nodes_with_access) / len(nodes) * 100
```

##### `normalize_metrics(metrics)`
Normalizes raw metrics to 0-100 scale and calculates final score.

**Normalization Ranges**:
```python
intersection_density: 0-500 → 0-100 (linear)
avg_block_length: 100-30 → 0-100 (inverse, shorter is better)
sidewalk_pct: 0-20 → 0-100 (linear, capped at 20%)
amenity_pct: 0-100 → 0-100 (linear)
```

**Weights**:
```python
score = (0.40 × intersection_norm +
         0.30 × block_norm +
         0.15 × sidewalk_norm +
         0.15 × amenity_norm)
```

**Returns**: (final_score, normalized_metrics_dict)

##### `run_walkability(place_name, output_dir)`
Main pipeline function.

**Workflow**:
1. Fetch city boundary from OSM
2. Fetch administrative boundaries (Kecamatan, Kelurahan)
3. Download road network graph
4. Download amenities (POIs)
5. Prepare Kelurahan polygons as analysis units
6. Spatial join: map nodes/edges to Kelurahan
7. Loop through each Kelurahan:
   - Extract nodes/edges for that Kelurahan
   - Calculate metrics
   - Normalize and score
8. Save results to GeoJSON and CSV
9. Generate standalone HTML map

**CRS Handling**:
- Input: WGS84 (EPSG:4326) from OSM
- Processing: Web Mercator (EPSG:3857) for metric calculations
- Output: WGS84 (EPSG:4326) for compatibility

### 2. app.py

#### Streamlit Components

##### `load_data()`
Cached data loader.
- **Cache**: `@st.cache_data` decorator
- **File**: `output/walkability_kelurahan.geojson`
- **Returns**: GeoDataFrame with all Kelurahan

##### Sidebar Filters
```python
# Kecamatan filter
kecamatan_list = sorted(data['kecamatan'].unique())
selected_kec = st.sidebar.selectbox("Pilih Kecamatan", ["Semua"] + kecamatan_list)

# Kelurahan filter (dynamic)
if selected_kec != "Semua":
    filtered_data = data[data['kecamatan'] == selected_kec]
    kelurahan_list = sorted(filtered_data['kelurahan'].unique())
    selected_kel = st.sidebar.selectbox("Pilih Kelurahan", ["Semua"] + kelurahan_list)
```

##### KPI Metrics
```python
avg_score = filtered_data['score'].mean()
avg_sidewalk = filtered_data['sidewalk_pct'].mean()
avg_int = filtered_data['intersection_density'].mean()
avg_amenity = filtered_data['amenity_pct'].mean()
```

##### Map Rendering
Uses `folium.Choropleth` with:
- **geo_data**: Filtered GeoDataFrame
- **columns**: ["kelurahan", "score"]
- **key_on**: "feature.properties.kelurahan"
- **fill_color**: "YlGn" (Yellow-Green gradient)

## Data Structures

### GeoDataFrame Schema

#### walkability_kelurahan.geojson
```
Columns:
- kelurahan (str): Kelurahan name
- unit_id (int): Unique identifier
- kecamatan (str): Parent Kecamatan name
- score (float): Final walkability score (0-100)
- intersection_density (float): Intersections per km²
- avg_block_length (float): Average edge length (m)
- sidewalk_pct (float): Sidewalk coverage (%)
- amenity_pct (float): Amenity access (%)
- n_int (int): Number of intersections
- n_block (int): Number of road segments
- n_sidewalk (int): Number of segments with sidewalk
- n_amenity (int): Number of nodes with amenity access
- geometry (Polygon): Kelurahan boundary
```

## Performance Considerations

### Execution Time
- **Data Download**: 2-3 minutes (depends on internet)
- **Spatial Processing**: 3-5 minutes (159 Kelurahan)
- **Total**: ~5-10 minutes

### Memory Usage
- **Peak RAM**: ~2-3 GB
- **Output Files**: ~5-10 MB total

### Optimization Opportunities
1. **Caching**: Implement local cache for OSM data
2. **Parallel Processing**: Use multiprocessing for Kelurahan loop
3. **Spatial Index**: Use R-tree for faster spatial joins
4. **Incremental Updates**: Only re-analyze changed Kelurahan

## API Dependencies

### OSMnx
```python
ox.geocode_to_gdf(place_name)
ox.graph_from_polygon(polygon, network_type="walk")
ox.features_from_polygon(polygon, tags={...})
ox.graph_to_gdfs(G, nodes=True, edges=True)
```

### GeoPandas
```python
gdf.to_crs(epsg=3857)
gpd.sjoin(gdf1, gdf2, how="inner", predicate="intersects")
gdf.to_file(filename, driver='GeoJSON')
```

### Folium
```python
folium.Map(location=[lat, lon], zoom_start=12)
folium.Choropleth(geo_data, data, columns, key_on, fill_color)
folium.features.GeoJsonTooltip(fields, aliases)
```

## Configuration

### Environment Variables
None currently used. Consider adding:
```python
OSM_CACHE_DIR = os.getenv('OSM_CACHE_DIR', './cache')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
```

### Constants
```python
# walkbility.py
WALK_BUFFER_M = 400  # Amenity access radius
ox.settings.timeout = 180  # OSM query timeout (seconds)
ox.settings.use_cache = True
ox.settings.log_console = False
```

## Error Handling

### Common Errors

#### OSM Timeout
```python
try:
    amenities = ox.features_from_polygon(boundary_poly, tags)
except Exception as e:
    print(f"Amenity fetch failed: {e}")
    amenities = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:3857")
```

#### Empty Kelurahan
```python
if kel_gdf.empty:
    print("ERROR: Tidak ada data Kelurahan")
    return
```

#### Spatial Join Failures
```python
# Handle duplicate matches
grid_points = grid_points.drop_duplicates(subset='orig_index')
# Handle missing columns
grid_points = grid_points.drop(columns='index_right', errors='ignore')
```

## Testing

### Unit Tests (Recommended)
```python
# test_metrics.py
def test_intersection_density():
    nodes = create_test_nodes()
    edges = create_test_edges()
    metrics = calculate_metrics(nodes, edges, 1_000_000, gpd.GeoDataFrame())
    assert metrics['intersection_density'] > 0

def test_normalization():
    metrics = {'intersection_density': 250, ...}
    score, norm = normalize_metrics(metrics)
    assert 0 <= score <= 100
```

### Integration Tests
```bash
# Test full pipeline
python walkbility.py
# Verify outputs
ls output/walkability_kelurahan.geojson
ls output/walkability_stats.csv
```

## Deployment

### Production Checklist
- [ ] Set `ox.settings.log_console = False`
- [ ] Implement error logging to file
- [ ] Add data validation checks
- [ ] Set up automated backups of output/
- [ ] Configure Streamlit for production (`--server.headless true`)
- [ ] Add authentication if needed
- [ ] Monitor memory usage

### Docker (Optional)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

## Future Enhancements

### Planned Features
1. **Historical Comparison**: Track walkability changes over time
2. **Route Planning**: Suggest walkable routes between points
3. **Accessibility Analysis**: Add wheelchair accessibility metrics
4. **Heat Maps**: Temporal analysis (day/night, weekday/weekend)
5. **API Endpoint**: REST API for external integrations

### Data Improvements
1. **Local Data Integration**: Combine with city government datasets
2. **Field Validation**: Ground-truth verification
3. **Sentiment Analysis**: Integrate citizen feedback
4. **Real-time Updates**: Automated OSM data refresh

## Contributing

### Code Style
- Follow PEP 8
- Use type hints where applicable
- Document functions with docstrings
- Keep functions under 50 lines

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Update documentation
5. Submit PR with clear description

---

**Version**: 2.0
**Last Updated**: 19 Januari 2026
