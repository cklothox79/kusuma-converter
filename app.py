import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Prakiraan Cuaca BMKG – Jawa Timur",
                   page_icon="🌦️",
                   layout="wide")

st.title("🌦️ Prakiraan Cuaca BMKG – Jawa Timur")

st.markdown(
    """
    Masukkan **nama desa/kota** di Jawa Timur untuk menampilkan lokasi pada peta.
    Marker akan tetap muncul walaupun aplikasi di-*rerun*.
    """
)

# -----------------------------
# 1️⃣  Geocoding Setup
# -----------------------------
geolocator = Nominatim(user_agent="bmkg_jatim_app")

# -----------------------------
# 2️⃣  Session State
# -----------------------------
if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.nama = None

# -----------------------------
# 3️⃣  Input Pencarian
# -----------------------------
lokasi_input = st.text_input("🟢 Masukkan Nama Desa/Kota (Jawa Timur)",
                              placeholder="contoh: Simogirang, Sidoarjo")

cari = st.button("🔍 Cari Lokasi")

if cari and lokasi_input:
    try:
        query = f"{lokasi_input}, Jawa Timur, Indonesia"
        lokasi = geolocator.geocode(query, timeout=15)
        if lokasi:
            st.session_state.lat = lokasi.latitude
            st.session_state.lon = lokasi.longitude
            st.session_state.nama = lokasi.address
            st.success(f"✅ Lokasi ditemukan: {lokasi.address}")
        else:
            st.warning("⚠️ Lokasi tidak ditemukan. Coba nama lain.")
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan geocoding: {e}")

# -----------------------------
# 4️⃣  Ambil Data dari Session
# -----------------------------
latitude = st.session_state.lat
longitude = st.session_state.lon
nama_lokasi = st.session_state.nama

# -----------------------------
# 5️⃣  Peta Folium
# -----------------------------
# Pusat peta di Jawa Timur jika belum ada lokasi
center_lat, center_lon = (-7.5, 112.7)
zoom_lvl = 7 if latitude is None else 12

m = folium.Map(location=[latitude or center_lat,
                         longitude or center_lon],
               zoom_start=zoom_lvl,
               tiles="cartodbpositron")

# Tambahkan marker bila sudah ada koordinat
if latitude and longitude:
    folium.Marker(
        [latitude, longitude],
        popup=nama_lokasi,
        tooltip="Lokasi Anda",
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(m)

# Tampilkan peta ke Streamlit
st_data = st_folium(m, width=950, height=550)

# -----------------------------
# 6️⃣  Informasi Koordinat
# -----------------------------
st.markdown("### 📍 Informasi Koordinat")
if latitude and longitude:
    st.write(f"**Latitude:** {latitude:.6f}")
    st.write(f"**Longitude:** {longitude:.6f}")
else:
    st.info("Masukkan nama desa/kota untuk menampilkan koordinat.")

# -----------------------------
# 7️⃣  Placeholder Prakiraan Cuaca (Tahap Berikutnya)
# -----------------------------
st.markdown("---")
st.subheader("🔮 Prakiraan Cuaca (Coming Next)")
st.caption(
    "Tahap selanjutnya: Ambil kode wilayah BMKG berdasarkan koordinat, "
    "kemudian menampilkan prakiraan cuaca hingga beberapa hari ke depan."
)
