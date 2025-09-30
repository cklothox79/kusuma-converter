import streamlit as st
import requests
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
from datetime import datetime

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", layout="wide")

st.title("🌦️ Prakiraan Cuaca BMKG – Pulau Jawa (Demo)")

# --- Fungsi Geocoding
@st.cache_data(show_spinner=False)
def geocode_location(place):
    geolocator = Nominatim(user_agent="bmkg_app")
    location = geolocator.geocode(place, timeout=10)
    if location:
        return location.latitude, location.longitude, location.address
    return None, None, None

# --- Fungsi Ambil Data BMKG
@st.cache_data(show_spinner=False)
def get_forecast(code):
    """
    Ambil prakiraan cuaca BMKG berdasarkan kode wilayah.
    """
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={code}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

# --- Fungsi Dummy Pencarian Kode BMKG
def get_bmkg_code(lat, lon):
    """
    Karena API adm BMKG tidak publik penuh,
    kita DEMO dengan kode wilayah tetap (Surabaya: 351517).
    Untuk real: lakukan pencocokan koordinat ke dataset BMKG.
    """
    # Contoh: wilayah Surabaya (bisa diganti data peta Jawa Timur)
    # Normally you'd search from a JSON of BMKG ADM4.
    return "351517"   # kode ADM4 Surabaya pusat

# --- Sidebar Input
st.sidebar.header("🔍 Pencarian Lokasi")
place = st.sidebar.text_input("Masukkan Nama Desa/Kota di Pulau Jawa", "Prambon, Sidoarjo")
run = st.sidebar.button("Cari Lokasi")

# --- Peta Awal
m = folium.Map(location=[-7.25, 112.75], zoom_start=7, tiles="OpenStreetMap")

lat = lon = address = None

if run and place:
    lat, lon, address = geocode_location(place)
    if lat and lon:
        folium.Marker([lat, lon], popup=address,
                      icon=folium.Icon(color="blue", icon="cloud")).add_to(m)

# Tampilkan Peta
st_map = st_folium(m, width=700, height=500)

# --- Jika Lokasi Ditemukan
if lat and lon:
    st.markdown(f"📍 **Koordinat:** {lat:.5f}, {lon:.5f}")
    st.markdown(f"🗺️ **Alamat:** {address}")

    # Ambil Kode BMKG
    try:
        code = get_bmkg_code(lat, lon)
        if not code:
            raise ValueError("Kode wilayah tidak ditemukan.")

        # Ambil Data Cuaca
        forecast = get_forecast(code)
        if forecast and isinstance(forecast, dict):
            st.success(f"✅ Data BMKG ditemukan untuk kode: {code}")

            # Tampilkan cuaca (cek struktur JSON)
            if "data" in forecast:
                data = forecast["data"]
                st.write("### 🌤️ Prakiraan Cuaca (Ringkasan)")
                for item in data:
                    tgl = item.get("tanggal", "-")
                    cuaca = item.get("cuaca", "-")
                    suhu = item.get("t", "-")
                    st.write(f"- **{tgl}** : {cuaca} | 🌡️ {suhu}°C")
            else:
                st.warning("⚠️ Struktur data BMKG berbeda, tidak bisa ditampilkan langsung.")
        else:
            st.error("❌ Tidak bisa mengambil data prakiraan dari BMKG.")
    except Exception as e:
        st.error(f"❌ Gagal ambil kode BMKG: {e}")
        st.warning("⚠️ Kode BMKG belum ditemukan. Coba lokasi lain.")
else:
    st.info("Masukkan nama desa/kota dan klik **Cari Lokasi** untuk mulai.")
