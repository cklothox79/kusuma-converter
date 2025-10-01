import streamlit as st
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="🌦️ Prakiraan Cuaca Interaktif BMKG", layout="wide")

# --- 1. Load CSV kode wilayah ---
@st.cache_data
def load_wilayah():
    df = pd.read_csv("kode_wilayah.csv", dtype=str)
    df.columns = [c.lower() for c in df.columns]
    return df

wilayah_df = load_wilayah()

st.title("🌦️ Prakiraan Cuaca Interaktif BMKG")

# --- 2. Input manual Desa, Kecamatan ---
st.subheader("📍 Input Manual")
user_input = st.text_input("Masukkan Nama Desa, Kecamatan", "Simogirang, Prambon")

kode = None
nama_wilayah = None

if user_input:
    try:
        desa, kecamatan = [x.strip().lower() for x in user_input.split(",")]
        # Cari desa dulu
        match = wilayah_df[wilayah_df["nama"].str.lower().str.contains(desa)]
        if not match.empty:
            kode = match.iloc[0]["kode"]
            nama_wilayah = match.iloc[0]["nama"]
            st.success(f"✅ Ditemukan kode wilayah: {kode} ({nama_wilayah})")
        else:
            st.warning("⚠️ Nama desa tidak ditemukan di database CSV")
    except Exception:
        st.warning("⚠️ Masukkan format: Desa, Kecamatan. Contoh: Simogirang, Prambon")

# --- 3. Klik Peta ---
st.subheader("🗺️ Klik Peta")
m = folium.Map(location=[-2, 118], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, width=700, height=450)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.write(f"📍 Koordinat dipilih: {lat:.4f}, {lon:.4f}")

    # Cari kecocokan nama terdekat di CSV (pakai geocoding)
    geolocator = Nominatim(user_agent="bmkg-app")
    loc = geolocator.reverse((lat, lon), language="id")
    if loc:
        nama_search = loc.raw.get("address", {}).get("village") or loc.raw.get("address", {}).get("town") or ""
        nama_search = nama_search.lower()
        match = wilayah_df[wilayah_df["nama"].str.lower().str.contains(nama_search)]
        if not match.empty:
            kode = match.iloc[0]["kode"]
            nama_wilayah = match.iloc[0]["nama"]
            st.success(f"✅ Ditemukan kode wilayah dari peta: {kode} ({nama_wilayah})")
        else:
            st.warning("⚠️ Wilayah tidak ditemukan di CSV")

# --- 4. Ambil Data BMKG ---
if kode:
    try:
        url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            if "data" in data and data["data"]:
                st.subheader(f"🌦️ Prakiraan Cuaca untuk {nama_wilayah}")
                st.json(data)  # sementara tampilkan JSON mentah
            else:
                st.error("❌ BMKG tidak mengembalikan data")
        else:
            st.error("❌ Gagal ambil data BMKG")
    except Exception as e:
        st.error(f"⚠️ Error ambil BMKG: {e}")
