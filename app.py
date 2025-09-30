import streamlit as st
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")

# --- 1. Load CSV kode wilayah ---
@st.cache_data
def load_kode_wilayah():
    # Pastikan kolom bernama 'kode' dan 'nama'
    df = pd.read_csv("data/kode_wilayah.csv", dtype=str)
    df.columns = [c.lower() for c in df.columns]
    return df

kode_df = load_kode_wilayah()

# --- 2. Input lokasi ---
lokasi = st.text_input("Masukkan Nama Desa/Kota", "Simogirang, Sidoarjo")

# --- 3. Geocoding ---
if lokasi:
    try:
        geolocator = Nominatim(user_agent="bmkg-app")
        loc = geolocator.geocode(lokasi)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.write(f"📍 Koordinat: {lat:.5f}, {lon:.5f}")
            st.write(f"🗺️ Alamat: {loc.address}")

            # --- 4. Cari kode wilayah terdekat berdasarkan nama ---
            # Ambil nama terakhir (misal desa/kota)
            nama_search = lokasi.split(",")[0].strip().lower()
            match = kode_df[kode_df['nama'].str.lower().str.contains(nama_search)]
            if not match.empty:
                kode = match.iloc[0]['kode']
                st.success(f"Kode Wilayah Ditemukan: {kode}")
            else:
                kode = None
                st.warning("⚠️ Kode wilayah tidak ditemukan di CSV")

            # --- 5. Peta dengan Marker ---
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker([lat, lon], popup=lokasi).add_to(m)
            st_folium(m, width=700, height=500)

            # --- 6. Ambil prakiraan BMKG (jika sudah punya endpoint) ---
            if kode:
                try:
                    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
                    r = requests.get(url, timeout=10)
                    if r.ok:
                        data = r.json()
                        st.write("✅ Data BMKG diterima")
                        st.json(data)
                    else:
                        st.error("❌ Gagal mengambil data BMKG.")
                except Exception as e:
                    st.error(f"❌ Error ambil BMKG: {e}")
        else:
            st.error("Lokasi tidak ditemukan.")
    except Exception as e:
        st.error(f"Geocoding error: {e}")
