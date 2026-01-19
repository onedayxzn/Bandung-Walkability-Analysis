# Panduan Pengguna - Bandung Walkability Dashboard

## Pendahuluan

Dashboard Walkability Bandung adalah aplikasi web interaktif yang memungkinkan Anda untuk mengeksplorasi dan menganalisis tingkat kemudahan berjalan kaki (walkability) di berbagai wilayah Kota Bandung.

Link akses: 

## Navigasi Dashboard

### 1. Header & KPI Cards
Di bagian atas dashboard, Anda akan melihat 4 kartu metrik utama:
- **Avg Walkability**: Rata-rata skor walkability wilayah yang dipilih
- **Avg Trotoar**: Rata-rata persentase cakupan trotoar
- **Kepadatan Persimpangan**: Rata-rata jumlah persimpangan per km²
- **Akses Fasilitas**: Rata-rata persentase akses ke fasilitas umum

### 2. Sidebar - Filter Wilayah

#### Filter Kecamatan
1. Klik dropdown "Pilih Kecamatan"
2. Pilih "Semua" untuk melihat seluruh Bandung
3. Atau pilih Kecamatan tertentu (contoh: Coblong, Sumur Bandung)

#### Filter Kelurahan
1. Setelah memilih Kecamatan, dropdown "Pilih Kelurahan" akan muncul
2. Pilih "Semua" untuk melihat semua Kelurahan di Kecamatan tersebut
3. Atau pilih Kelurahan spesifik untuk analisis detail

### 3. Peta Interaktif

#### Memahami Warna
- **Hijau Tua**: Skor walkability tinggi (85-100)
- **Hijau Muda**: Skor walkability sedang (70-85)
- **Kuning**: Skor walkability rendah (50-70)
- **Merah**: Skor walkability sangat rendah (0-50)

#### Interaksi Peta
- **Zoom In/Out**: Gunakan tombol +/- atau scroll mouse
- **Pan**: Klik dan drag untuk menggeser peta
- **Hover**: Arahkan kursor ke poligon untuk melihat detail:
  - Nama Kecamatan
  - Nama Kelurahan
  - Skor Walkability
  - % Trotoar
  - % Fasilitas

### 4. Grafik Distribusi Skor
Histogram di bagian bawah menunjukkan distribusi skor walkability:
- Sumbu X: Rentang skor (0-100)
- Sumbu Y: Jumlah Kelurahan
- Warna hijau menunjukkan frekuensi

### 5. Tabel Low Walkability Areas
Tabel menampilkan 10 Kelurahan dengan skor terendah:
- Berguna untuk identifikasi area prioritas perbaikan
- Menampilkan Kecamatan, Kelurahan, dan Skor

## Contoh Penggunaan

### Kasus 1: Analisis Kecamatan
**Tujuan**: Membandingkan walkability antar Kecamatan

1. Pilih "Semua" di filter Kecamatan
2. Perhatikan peta - identifikasi area hijau tua (walkable) vs kuning/merah
3. Catat KPI "Avg Walkability" sebagai baseline
4. Ganti filter ke Kecamatan tertentu (misal: Coblong)
5. Bandingkan KPI baru dengan baseline
6. Ulangi untuk Kecamatan lain

### Kasus 2: Identifikasi Area Prioritas
**Tujuan**: Menemukan Kelurahan yang perlu perbaikan infrastruktur

1. Pilih "Semua" di filter Kecamatan
2. Scroll ke tabel "Top Low Walkability Areas"
3. Identifikasi Kelurahan dengan skor < 80
4. Klik Kelurahan tersebut di filter untuk melihat detail
5. Perhatikan metrik spesifik (trotoar, fasilitas, persimpangan)
6. Gunakan data untuk rekomendasi perbaikan

### Kasus 3: Analisis Detail Kelurahan
**Tujuan**: Memahami faktor walkability di wilayah spesifik

1. Pilih Kecamatan (contoh: Sumur Bandung)
2. Pilih Kelurahan (contoh: Braga)
3. Perhatikan KPI individual:
   - Skor tinggi + trotoar tinggi = infrastruktur pejalan kaki baik
   - Skor tinggi + fasilitas tinggi = area mixed-use
   - Skor rendah + persimpangan rendah = area suburban/perifer
4. Hover di peta untuk konfirmasi visual

## Interpretasi Metrik

### Skor Walkability (0-100)
- **90-100**: Sangat Walkable (pusat kota, area komersial)
- **80-89**: Walkable (area residensial padat)
- **70-79**: Cukup Walkable (area residensial sedang)
- **< 70**: Kurang Walkable (area pinggiran, industrial)

### Kepadatan Persimpangan
- **> 200/km²**: Jaringan jalan sangat terhubung
- **100-200/km²**: Jaringan jalan baik
- **< 100/km²**: Jaringan jalan terbatas

### % Trotoar
- **> 10%**: Cakupan trotoar baik (data OSM)
- **5-10%**: Cakupan trotoar sedang
- **< 5%**: Cakupan trotoar rendah (atau data tidak lengkap)

### % Fasilitas
- **> 90%**: Akses fasilitas sangat baik
- **80-90%**: Akses fasilitas baik
- **< 80%**: Akses fasilitas terbatas

## Tips & Trik

### Performa
- Untuk performa optimal, filter ke Kecamatan spesifik saat menganalisis detail
- Refresh halaman (F5) jika peta tidak merespons

### Export Data
- Untuk export data, gunakan file `output/walkability_stats.csv`
- Buka di Excel atau Google Sheets untuk analisis lanjutan

### Screenshot
- Gunakan Snipping Tool (Windows) atau Screenshot (Mac) untuk capture peta
- Berguna untuk presentasi atau laporan

## Troubleshooting

### Peta Tidak Muncul
1. Pastikan file `output/walkability_kelurahan.geojson` ada
2. Refresh halaman (F5)
3. Restart dashboard

### Filter Tidak Bekerja
1. Pastikan data sudah ter-load (lihat spinner di pojok kanan atas)
2. Clear cache Streamlit: Settings → Clear Cache
3. Restart dashboard

### Data Tidak Update
1. Jalankan ulang `python walkbility.py` untuk generate data baru
2. Restart dashboard
3. Hard refresh browser (Ctrl+Shift+R)

## FAQ

**Q: Kenapa beberapa Kelurahan memiliki skor 0?**
A: Kemungkinan data OSM tidak lengkap atau Kelurahan tersebut adalah area non-residensial (kantor pemerintah, dll)

**Q: Apakah skor walkability bisa diupdate?**
A: Ya, jalankan ulang `walkbility.py` untuk mendapatkan data OSM terbaru

**Q: Bagaimana cara export peta?**
A: Gunakan file `walkability_map.html` di folder output, atau screenshot dari dashboard

**Q: Apakah bisa analisis kota lain?**
A: Ya, edit parameter `place_name` di `walkbility.py` (baris 268)



**Versi**: 2.0 (Kelurahan-based)
**Terakhir Diperbarui**: 19 Januari 2026
