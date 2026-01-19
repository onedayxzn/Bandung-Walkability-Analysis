# Bandung Walkability Analysis

Sistem analisis walkability (kemudahan berjalan kaki) untuk Kota Bandung menggunakan data OpenStreetMap dan batas administrasi resmi (Kelurahan).


##  Fitur Utama

- **Analisis Berbasis Kelurahan**: Menggunakan 159 batas administrasi resmi Kelurahan di Bandung
- **Metrik Komprehensif**: 
  - Kepadatan persimpangan jalan
  - Panjang rata-rata blok
  - Persentase trotoar
  - Akses ke fasilitas umum
- **Dashboard Interaktif**: Streamlit app dengan filter hierarkis (Kecamatan → Kelurahan)
- **Visualisasi Peta**: Choropleth map dengan poligon administratif asli
- **Export Data**: GeoJSON dan CSV untuk integrasi GIS

##  Hasil Analisis

### Statistik Keseluruhan
- **Total Kelurahan**: 159
- **Rata-rata Skor**: 85.6/100
- **Rentang Skor**: 0 - 100
- **Standar Deviasi**: 14.7

### Top 5 Kelurahan Terbaik
1. **Braga** (Sumur Bandung) - 100.0
2. **Babakan Ciamis** (Sumur Bandung) - 100.0
3. **Citarum** (Bandung Wetan) - 100.0
4. **Cihapit** (Bandung Wetan) - 100.0
5. **Lingkar Selatan** (Lengkong) - 100.0

##  Instalasi

### Persyaratan Sistem
- Python 3.8+
- Virtual environment (recommended)

### Langkah Instalasi

1. **Clone atau download project**
```bash
cd Bandung_Urban_Planing
```

2. **Buat virtual environment**
```bash
python -m venv venv
```

3. **Aktifkan virtual environment**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install osmnx networkx geopandas pandas numpy folium tqdm streamlit streamlit-folium plotly
```

##  Cara Penggunaan

### 1. Menjalankan Analisis

Untuk menghasilkan data walkability baru:

```bash
python walkbility.py
```

**Output**:
- `output/walkability_kelurahan.geojson` - Data spasial dengan poligon Kelurahan
- `output/walkability_stats.csv` - Tabel statistik per Kelurahan
- `output/walkability_map.html` - Peta interaktif standalone

**Waktu Eksekusi**: ~5-10 menit (tergantung koneksi internet)

### 2. Menjalankan Dashboard

Untuk membuka dashboard interaktif:

```bash
streamlit run app.py
```

Dashboard akan terbuka di browser pada `http://localhost:8501`

**Fitur Dashboard**:
- Filter per Kecamatan dan Kelurahan
- KPI cards dengan statistik real-time
- Peta choropleth interaktif
- Grafik distribusi skor
- Tabel area dengan walkability rendah

### 3. Menghentikan Dashboard

```bash
# Tekan Ctrl+C di terminal
# Atau gunakan Task Manager untuk kill process streamlit.exe
```

### Akses langsung
https://bandung-walkability-analysis.streamlit.app/

##  Struktur File

```
Bandung_Urban_Planing/
├── walkbility.py           # Script analisis utama
├── app.py                  # Streamlit dashboard
├── output/                 # Folder hasil analisis
│   ├── walkability_kelurahan.geojson
│   ├── walkability_stats.csv
│   └── walkability_map.html
├── venv/                   # Virtual environment
└── README.md              # Dokumentasi ini
```

##  Konfigurasi

### Mengubah Parameter Analisis

Edit file `walkbility.py`:

```python
# Baris 19-20
WALK_BUFFER_M = 400  # Radius akses fasilitas (meter)
GRID_SIZE_M = 500    # Tidak digunakan (legacy)
```

### Mengubah Bobot Metrik

Edit fungsi `normalize_metrics()` di `walkbility.py` (baris 108-128):

```python
# Bobot default:
# - Intersection Density: 40%
# - Average Block Length: 30%
# - Sidewalk Coverage: 15%
# - Amenity Access: 15%
```

##  Metodologi

### Sumber Data
- **Jaringan Jalan**: OpenStreetMap (OSMnx)
- **Fasilitas Umum**: OSM POI (amenity, shop, leisure, tourism)
- **Batas Administrasi**: OSM administrative boundaries (level 6 & 7)

### Metrik Walkability

1. **Intersection Density** (Kepadatan Persimpangan)
   - Jumlah persimpangan per km²
   - Normalisasi: 0-500 intersections/km²

2. **Average Block Length** (Panjang Blok)
   - Rata-rata panjang segmen jalan
   - Normalisasi: 30-100 meter (lebih pendek = lebih baik)

3. **Sidewalk Coverage** (Cakupan Trotoar)
   - Persentase jalan dengan data trotoar
   - Normalisasi: 0-100%

4. **Amenity Access** (Akses Fasilitas)
   - Persentase node dalam radius 400m dari fasilitas
   - Normalisasi: 0-100%

### Formula Skor Akhir

```
Score = (0.40 × Intersection_Norm) + 
        (0.30 × Block_Norm) + 
        (0.15 × Sidewalk_Norm) + 
        (0.15 × Amenity_Norm)
```

Skor akhir: 0-100 (lebih tinggi = lebih walkable)

##  Integrasi GIS

### Membuka di QGIS

1. Buka QGIS
2. Layer → Add Layer → Add Vector Layer
3. Pilih `output/walkability_kelurahan.geojson`
4. Style berdasarkan kolom `score`

### Export ke Shapefile

```python
import geopandas as gpd

gdf = gpd.read_file('output/walkability_kelurahan.geojson')
gdf.to_file('output/walkability.shp')
```

##  Troubleshooting

### Error: "No module named 'osmnx'"
```bash
pip install osmnx
```

### Error: Timeout saat download data
Edit `walkbility.py` baris 14:
```python
ox.settings.timeout = 300  # Tingkatkan timeout ke 5 menit
```

### Dashboard tidak menampilkan data
Pastikan file `output/walkability_kelurahan.geojson` ada:
```bash
python walkbility.py  # Generate ulang data
```

### Streamlit error: "Address already in use"
Gunakan port berbeda:
```bash
streamlit run app.py --server.port 8502
```

##  Referensi

- **OSMnx**: Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126-139.
- **Walkability Metrics**: Frank, L. D., et al. (2010). The development of a walkability index: application to the Neighborhood Quality of Life Study. *British Journal of Sports Medicine*, 44(13), 924-933.


##  Kontributor

Dikembangkan menggunakan:
- Python 3.x
- OSMnx untuk data OpenStreetMap
- GeoPandas untuk analisis spasial
- Streamlit untuk dashboard interaktif

##  Kontak

Untuk pertanyaan atau saran, silakan buka issue di repository ini.

---

**Last Updated**: 19 Januari 2026
