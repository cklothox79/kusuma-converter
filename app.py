import streamlit as st
import pandas as pd
import requests
from streamlit_folium import st_folium
import folium
from geopy.distance import geodesic

# ==============================
# Load kode wilayah
# ==============================
@st.cache_data
def load_wilayah():
    df = pd.read_csv("kode_wilayah.csv", dtype=str)
    df = df.dropna()
    return df

wilayah_df = load_wilayah()

# ==============================
# Fungsi cari lokasi terdekat
# ==============================
def cari_wilayah_terdekat(lat, lon):
    wilayah_df["lat"] = wilayah_df["lat"].astype(float)
    wilayah_df["lon"] = wilayah_df["lon"].astype(float)

    wilayah_df["distance"] = wilayah_df.apply(
        lambda row: geodesic((lat, lon), (row["lat"], row["lon"])).meters, axis=1
    )
    wilayah_df_sorted = wilayah_df.sort_values("distance")
    return wilayah_df_sorted.iloc[0]  # ambil terdekat

# ==============================
# Ambil data BMKG
# ==============================
def ambil_data_bmkg(adm_code):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm_code}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"⚠️ Gagal ambil data BMKG: {e}")
        return None

# ==============================
# UI
# ==============================
st.title("🌦️ Prakiraan Cuaca Interaktif BMKG")

tab1, tab2 = st.tabs(["📍 Input Manual", "🗺️ Klik Peta"])

with tab1:
    lokasi_input = st.text_input("Masukkan Nama Desa, Kecamatan", "Simogirang, Prambon")
    if lokasi_input:
        desa, kecamatan = [x.strip() for x in lokasi_input.split(",")]
        row = wilayah_df[
            (wilayah_df["desa"].str.lower() == desa.lower()) &
            (wilayah_df["kecamatan"].str.lower() == kecamatan.lower())
        ]
        if not row.empty:
            kode = row.iloc[0]["kode"]
            data = ambil_data_bmkg(kode)
            if data:
                st.success(f"✅ Data BMKG untuk {desa}, {kecamatan}")
                st.json(data)  # tampilkan JSON (nanti bisa rapikan tabel/visual)
        else:
            st.warning("❌ Wilayah tidak ditemukan di database.")

with tab2:
    st.write("Klik di peta untuk memilih lokasi:")
    m = folium.Map(location=[-7.44, 112.58], zoom_start=11)
    folium.Marker([-7.44, 112.58], tooltip="Simogirang, Prambon").add_to(m)

    map_data = st_folium(m, width=700, height=450)

    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]

        st.info(f"📍 Titik dipilih: {lat:.4f}, {lon:.4f}")

        wilayah = cari_wilayah_terdekat(lat, lon)
        st.write(f"🗂️ Lokasi terdekat: **{wilayah['desa']}, {wilayah['kecamatan']}**")

        kode = wilayah["kode"]
        data = ambil_data_bmkg(kode)
        if data:
            st.success(f"✅ Data BMKG untuk {wilayah['desa']}, {wilayah['kecamatan']}")
            st.json(data)  # nanti bisa tampilkan tabel/visual
