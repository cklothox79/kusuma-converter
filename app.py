import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="⛅", layout="wide")

# -----------------------------------------
# Fungsi API BMKG
# -----------------------------------------
BASE_URL = "https://api-apps.bmkg.go.id/publik/prakiraan-cuaca"

def get_wilayah(adm_name, level, parent_code=""):
    """
    Pencarian kode wilayah BMKG berdasarkan nama dan level.
    level: adm1, adm2, adm3, adm4
    """
    try:
        url = f"{BASE_URL}/wilayah"
        params = {"nama": adm_name, "level": level}
        if parent_code:
            params["parent"] = parent_code
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data and "data" in data and len(data["data"]) > 0:
            return data["data"][0]  # ambil hasil pertama
    except Exception as e:
        st.warning(f"Gagal mencari {level}: {e}")
    return None


def get_cuaca(adm4):
    """Ambil data prakiraan cuaca berdasarkan kode desa (adm4)."""
    try:
        url = f"{BASE_URL}"
        params = {"adm4": adm4}
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"⚠️ Gagal mengambil data cuaca: {e}")
        return None


# -----------------------------------------
# Input Pengguna
# -----------------------------------------
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Wilayah")

prov = st.text_input("Provinsi", "Jawa Timur")
kab = st.text_input("Kabupaten/Kota", "Sidoarjo")
kec = st.text_input("Kecamatan", "Prambon")
desa = st.text_input("Kelurahan/Desa", "Simogirang")

if st.button("🔍 Cari Prakiraan Cuaca"):
    with st.spinner("Mencari data wilayah..."):
        # Cari Provinsi
        w_prov = get_wilayah(prov, "adm1")
        if not w_prov:
            st.error("Provinsi tidak ditemukan.")
            st.stop()

        w_kab = get_wilayah(kab, "adm2", w_prov["adm1"])
        if not w_kab:
            st.error("Kab/Kota tidak ditemukan.")
            st.stop()

        w_kec = get_wilayah(kec, "adm3", w_kab["adm2"])
        if not w_kec:
            st.error("Kecamatan tidak ditemukan.")
            st.stop()

        w_desa = get_wilayah(desa, "adm4", w_kec["adm3"])
        if not w_desa:
            st.error("Desa tidak ditemukan.")
            st.stop()

        st.success(
            f"✅ Wilayah ditemukan: {w_prov['nama']} > {w_kab['nama']} > "
            f"{w_kec['nama']} > {w_desa['nama']}"
        )

    # -----------------------------------------
    # Ambil data cuaca
    # -----------------------------------------
    with st.spinner("Mengambil data prakiraan cuaca..."):
        cuaca = get_cuaca(w_desa["adm4"])

    if cuaca and "data" in cuaca:
        lokasi = cuaca["lokasi"]
        st.subheader("📍 Lokasi")
        st.write(
            f"Provinsi: **{lokasi['provinsi']}**, "
            f"Kab/Kota: **{lokasi['kotkab']}**, "
            f"Kecamatan: **{lokasi['kecamatan']}**, "
            f"Desa: **{lokasi['desa']}**"
        )
        st.write(f"Koordinat: {lokasi['lat']}, {lokasi['lon']}")

        # Ambil data cuaca jam-jaman (hari pertama)
        jam_jaman = []
        for group in cuaca["data"]:
            for item in group["cuaca"][0]:  # ambil blok pertama (hari ini)
                jam_jaman.append({
                    "Waktu": item["local_datetime"],
                    "Suhu (°C)": item["t"],
                    "Kelembapan (%)": item["hu"],
                    "Arah Angin": item["wd"],
                    "Kecepatan (m/s)": item["ws"],
                    "Cuaca": item["weather_desc"],
                    "Icon": item["image"]
                })

        df = pd.DataFrame(jam_jaman)

        st.subheader("📊 Prakiraan Cuaca (Hari Ini)")
        st.dataframe(df.drop(columns=["Icon"]), use_container_width=True)

        # Tampilkan kartu cuaca
        st.subheader("🖼️ Kartu Cuaca")
        cols = st.columns(4)
        for i, row in df.iterrows():
            with cols[i % 4]:
                st.markdown(
                    f"**{row['Waktu']}**  \n"
                    f"🌡️ {row['Suhu (°C)']} °C  \n"
                    f"💧 {row['Kelembapan (%)']}%  \n"
                    f"💨 {row['Kecepatan (m/s)']} m/s  \n"
                    f"☁️ {row['Cuaca']}"
                )
                st.image(row["Icon"], width=60)
