import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")
st.title("🌦️ Prakiraan Cuaca BMKG – Jawa Timur")

# --- Geocoding Input ---
geolocator = Nominatim(user_agent="cuaca_bmkg_jatim")

with st.sidebar:
    st.header("🔍 Cari Lokasi")
    lokasi_input = st.text_input("Masukkan nama desa/kota di Jawa Timur")
    tombol_cari = st.button("Cari Lokasi")

latitude = longitude = None
nama_lokasi = None

if tombol_cari and lokasi_input:
    try:
        lokasi = geolocator.geocode(f"{lokasi_input}, Jawa Timur, Indonesia")
        if lokasi:
            latitude = lokasi.latitude
            longitude = lokasi.longitude
            nama_lokasi = lokasi.address
            st.sidebar.success(f"Lokasi ditemukan: {nama_lokasi}")
        else:
            st.sidebar.error("Lokasi tidak ditemukan, coba nama lain.")
    except Exception as e:
        st.sidebar.error(f"Error geocoding: {e}")

# --- Peta Dasar ---
m = folium.Map(location=[-7.5,112.7], zoom_start=7)
if latitude and longitude:
    folium.Marker([latitude, longitude],
                  popup=nama_lokasi,
                  tooltip="Lokasi Anda").add_to(m)

st_data = st_folium(m, width=900, height=500)

# ====================
# === Prakiraan Cuaca ===
# ====================

# Contoh Kode Wilayah ADM4 BMKG (sebagian kecil Jawa Timur)
# (Data nyata bisa diperluas; ini contoh untuk demo)
kode_wilayah_jatim = {
    "Surabaya": "3515",
    "Sidoarjo": "3516",
    "Malang": "3507",
    "Kediri": "3506",
    "Banyuwangi": "3510",
    "Jember": "3511"
}

def get_nearest_kode(lat, lon):
    """
    Cari kode wilayah terdekat dari list statis sederhana.
    Nanti bisa diganti dengan pencarian otomatis.
    """
    # Di sini kita hanya memilih Surabaya sebagai default demo
    # atau kamu bisa kembangkan ke perhitungan jarak
    return "3515"

def get_forecast(kode):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

if latitude and longitude:
    with st.spinner("Mengambil data prakiraan cuaca BMKG..."):
        kode = get_nearest_kode(latitude, longitude)
        try:
            data_cuaca = get_forecast(kode)

            # --- Parsing sederhana ---
            records = []
            for area in data_cuaca.get("data", []):
                nama = area.get("lokasi", "")
                for prakiraan in area.get("cuaca", []):
                    waktu = prakiraan.get("datetime")
                    cuaca = prakiraan.get("weather")
                    suhu = prakiraan.get("temperature")
                    kelembapan = prakiraan.get("humidity")
                    records.append({
                        "Lokasi": nama,
                        "Waktu": datetime.fromisoformat(waktu).strftime("%d-%m %H:%M"),
                        "Cuaca": cuaca,
                        "Suhu (°C)": suhu,
                        "Kelembapan (%)": kelembapan
                    })

            if records:
                df = pd.DataFrame(records)
                st.subheader(f"📊 Prakiraan Cuaca BMKG – Kode {kode}")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Data prakiraan belum tersedia.")
        except Exception as e:
            st.error(f"Gagal mengambil data BMKG: {e}")
