import pandas as pd
import time
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# === KONFIGURASI DASAR ===
INPUT_FILE = "kode_wilayah_jatim.csv"
OUTPUT_FILE = "kode_wilayah_jatim_with_coords.csv"
CACHE_FILE = "cache_geocode.csv"
SLEEP_TIME = 1.2  # detik (batas aman API OpenStreetMap)

# === INISIALISASI DATA ===
df = pd.read_csv(INPUT_FILE)
df.columns = ['kode', 'nama']

# Pastikan kolom lat lon ada
if 'lat' not in df.columns:
    df['lat'] = None
if 'lon' not in df.columns:
    df['lon'] = None

# === BACA CACHE SEBELUMNYA (JIKA ADA) ===
if os.path.exists(CACHE_FILE):
    cache = pd.read_csv(CACHE_FILE)
else:
    cache = pd.DataFrame(columns=['nama', 'lat', 'lon'])

# === INISIALISASI NOMINATIM ===
geolocator = Nominatim(user_agent="jatim_geocoder")

def get_location_cached(nama):
    """Ambil koordinat dari cache, kalau belum ada → ambil dari API."""
    # Cek di cache
    if nama in cache['nama'].values:
        row = cache.loc[cache['nama'] == nama].iloc[0]
        return row['lat'], row['lon']
    
    # Kalau belum ada di cache → ambil dari API
    try:
        query = f"{nama}, Jawa Timur, Indonesia"
        print(f"🔍 Mencari koordinat: {query}")
        loc = geolocator.geocode(query, timeout=10)
        if loc:
            lat, lon = loc.latitude, loc.longitude
        else:
            lat, lon = None, None
    except (GeocoderTimedOut, GeocoderServiceError):
        print("⚠️ Timeout atau error koneksi, mencoba ulang...")
        time.sleep(3)
        return get_location_cached(nama)
    
    # Simpan ke cache agar cepat kalau script dijalankan ulang
    new_cache = pd.DataFrame([[nama, lat, lon]], columns=['nama', 'lat', 'lon'])
    global cache
    cache = pd.concat([cache, new_cache], ignore_index=True)
    cache.to_csv(CACHE_FILE, index=False)
    
    time.sleep(SLEEP_TIME)
    return lat, lon

# === PROSES PENGAMBILAN KOORDINAT ===
for i, row in df.iterrows():
    if pd.notna(row['lat']) and pd.notna(row['lon']):
        continue  # sudah ada
    nama = str(row['nama'])
    lat, lon = get_location_cached(nama)
    df.at[i, 'lat'] = lat
    df.at[i, 'lon'] = lon
    df.to_csv(OUTPUT_FILE, index=False)

print("\n✅ Semua koordinat berhasil diproses dan disimpan di:", OUTPUT_FILE)
print("📁 Cache tersimpan di:", CACHE_FILE)
