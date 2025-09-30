import streamlit as st
import requests
import json
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG – Pulau Jawa",
                   page_icon="🌦️", layout="wide")

st.title("🌦️ Prakiraan Cuaca BMKG – Pulau Jawa")

# ====== Data Wilayah Pulau Jawa (sementara lokal) ======
# Format: {provinsi: {kabupaten: kode_adm4_BMKG}}
# Kode di bawah hanya CONTOH (gunakan kode resmi BMKG jika sudah tersedia)
wilayah_jawa = {
    "Banten": {
        "Kota Serang": "36.71.0000",
        "Kota Tangerang": "36.72.0000"
    },
    "DKI Jakarta": {
        "Jakarta Pusat": "31.71.0000",
        "Jakarta Barat": "31.72.0000"
    },
    "Jawa Barat": {
        "Bandung": "32.73.0000",
        "Bogor": "32.71.0000"
    },
    "Jawa Tengah": {
        "Semarang": "33.74.0000",
        "Surakarta": "33.75.0000"
    },
    "DI Yogyakarta": {
        "Yogyakarta": "34.71.0000"
    },
    "Jawa Timur": {
        "Surabaya": "35.78.0000",
        "Malang": "35.73.0000"
    }
}

# ====== Sidebar Pilihan ======
st.sidebar.header("🟢 Pilih Wilayah")
prov = st.sidebar.selectbox("Provinsi", list(wilayah_jawa.keys()))
kab = st.sidebar.selectbox("Kota/Kabupaten", list(wilayah_jawa[prov].keys()))

kode_wilayah = wilayah_jawa[prov][kab]

# ====== Fungsi Ambil Data Prakiraan BMKG ======
@st.cache_data(ttl=600)
def get_forecast(adm4):
    """
    Contoh endpoint BMKG publik (update sesuai dokumentasi BMKG terbaru)
    """
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

# ====== Peta Folium ======
# (Lokasi default Jawa Tengah, bisa diperluas dengan koordinat real)
m = folium.Map(location=[-7.25, 112.75], zoom_start=6, tiles="OpenStreetMap")
st_map = st_folium(m, height=400, width=800)

# ====== Tampilkan Prakiraan Cuaca ======
if st.sidebar.button("🔎 Tampilkan Prakiraan"):
    try:
        data = get_forecast(kode_wilayah)
        st.subheader(f"Prakiraan Cuaca – {kab}, {prov}")
        st.json(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Gagal mengambil data prakiraan BMKG: {e}")
