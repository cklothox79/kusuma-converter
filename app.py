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
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={code}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

# --- Dummy Kode BMKG (contoh Surabaya)
def get_bmkg_code(lat, lon):
    # TODO: ganti dengan pencarian ADM4 sebenarnya
    return "351517"   # kode ADM4 Surabaya pusat

# --- Session State untuk menyimpan lokasi terakhir
if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.address = None

# --- Sidebar Input
st.sidebar.header("🔍 Pencarian Lokasi")
place = st.sidebar.text_input("Masukkan Nama Desa/Kota di Pulau Jawa", "Prambon, Sidoarjo")
if st.sidebar.button("Cari Lokasi"):
    lat, lon, address = geocode_location(place)
    if lat and lon:
        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.address = address
    else:
        st.warning("Lokasi tidak ditemukan. Coba kata kunci lain.")

# --- Gunakan lokasi yang tersimpan
lat = st.session_state.lat
lon = st.session_state.lon
address = st.session_state.address

# --- Peta
m = folium.Map(location=[-7.25, 112.75], zoom_start=7, tiles="OpenStreetMap")
if lat and lon:
    folium.Marker([lat, lon], popup=address,
                  icon=folium.Icon(color="blue", icon="cloud")).add_to(m)

st_map = st_folium(m, width=700, height=500)

# --- Tampilkan Data Cuaca Jika Ada Lokasi
if lat and lon:
    st.markdown(f"📍 **Koordinat:** {lat:.5f}, {lon:.5f}")
    st.markdown(f"🗺️ **Alamat:** {address}")

    try:
        code = get_bmkg_code(lat, lon)
        if not code:
            raise ValueError("Kode wilayah tidak ditemukan.")

        forecast = get_forecast(code)
        if forecast and isinstance(forecast, dict):
            st.success(f"✅ Data BMKG ditemukan untuk kode: {code}")

            if "data" in forecast:
                st.write("### 🌤️ Prakiraan Cuaca (Ringkasan)")
                for item in forecast["data"]:
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
else:
    st.info("Masukkan nama desa/kota dan klik **Cari Lokasi** untuk mulai.")
