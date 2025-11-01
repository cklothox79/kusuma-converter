import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import time

st.set_page_config(page_title="🌦️ Prakiraan Harian & Dinamika Atmosfer — Jawa Timur", layout="wide")
st.title("🌦️ Prakiraan Harian & Dinamika Atmosfer — Jawa Timur")
st.write("Fusion: BMKG (jika tersedia) + Open-Meteo. Mudah dipahami publik — input cukup nama desa/kecamatan/kabupaten.")

# -------------------------
# 1) Load local kode_wilayah.csv (root repo)
# -------------------------
CSV_PATH = "kode_wilayah.csv"  # file ada di root repo; ubah path jika dipindah ke /data/

@st.cache_data(ttl=3600)
def load_wilayah(csv_path=CSV_PATH):
    try:
        df = pd.read_csv(csv_path, dtype=str, encoding='utf-8')
        # normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        if 'kode' not in df.columns or 'nama' not in df.columns:
            st.error("File CSV perlu kolom minimal: 'kode' dan 'nama'.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Gagal membaca {csv_path}: {e}")
        return pd.DataFrame()

wilayah_df = load_wilayah()

if wilayah_df.empty:
    st.stop()

# -------------------------
# 2) Input user & cari kecocokan (contains search)
# -------------------------
st.sidebar.header("Pencarian Lokasi")
nama_input = st.sidebar.text_input("Ketik nama desa/kecamatan/kabupaten (contoh: Simogirang)", "")

# optional: show examples top 10
if st.sidebar.button("Tampilkan contoh nama (10 teratas)"):
    st.sidebar.write(wilayah_df["nama"].dropna().head(50).tolist()[:50])

selected_row = None
if nama_input:
    matches = wilayah_df[wilayah_df["nama"].str.contains(nama_input, case=False, na=False)]
    if len(matches) == 0:
        st.warning("Nama daerah tidak ditemukan di CSV lokal. Coba ejaan lain atau tambahkan kata kunci kabupaten/kota.")
    elif len(matches) == 1:
        selected_row = matches.iloc[0]
    else:
        # jika banyak hasil, beri pilihan
        choice = st.sidebar.selectbox("Pilih hasil yang tepat:", matches["nama"].tolist())
        selected_row = matches[matches["nama"] == choice].iloc[0]

# -------------------------
# 3) Geocoding using OpenStreetMap Nominatim API
# -------------------------
def geocode_nominatim(name):
    """Geocode a place name to latitude and longitude using OpenStreetMap Nominatim."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(name)}&format=json&addressdetails=1&limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data:
            lat = data[0].get("lat")
            lon = data[0].get("lon")
            return float(lat), float(lon)
    except Exception as e:
        st.warning(f"Error geocoding {name}: {e}")
    return None, None

# -------------------------
# 4) Apply geocoding for all regions in the CSV
# -------------------------
def apply_geocoding(df):
    latitudes = []
    longitudes = []
    for _, row in df.iterrows():
        # Combine the name with full location information
        full_name = row['nama'] + ", Jawa Timur, Indonesia"
        lat, lon = geocode_nominatim(full_name)
        latitudes.append(lat)
        longitudes.append(lon)
        time.sleep(1)  # Sleep to avoid API rate limit
    df['lat'] = latitudes
    df['lon'] = longitudes
    return df

# Apply geocoding to the dataframe
wilayah_df = apply_geocoding(wilayah_df)

# Save the new CSV with lat and lon filled
output_path = '/mnt/data/kode_wilayah_jatim_with_coords.csv'
wilayah_df.to_csv(output_path, index=False)

# -------------------------
# 5) Display the new CSV path
# -------------------------
st.write("Geocoding completed. The results are saved in the file:", output_path)

