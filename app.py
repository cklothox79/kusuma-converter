import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Cuaca & Dinamika Atmosfer Jawa Timur", layout="wide")

st.title("🌦️ Prakiraan Cuaca & Dinamika Atmosfer – Jawa Timur")

# --- Load data wilayah dari GitHub ---
# (pastikan file kamu sudah diunggah di repo GitHub)
url = "https://raw.githubusercontent.com/cklothoz79/tafor_warr/main/kode_wilayah.csv"
wilayah_df = pd.read_csv(url)

# --- Input nama daerah ---
nama_input = st.text_input("Masukkan nama daerah (desa/kecamatan/kabupaten):", "").strip()

if nama_input:
    hasil = wilayah_df[wilayah_df["nama"].str.contains(nama_input, case=False, na=False)]

    if len(hasil) == 0:
        st.warning("❌ Nama daerah tidak ditemukan. Coba masukkan nama lain.")
    else:
        # Ambil hasil pertama
        nama_wilayah = hasil.iloc[0]["nama"]
        kode_wilayah = hasil.iloc[0]["kode"]

        st.success(f"📍 Wilayah ditemukan: **{nama_wilayah}** (Kode: {kode_wilayah})")

        # --- Contoh koordinat sementara (bisa diganti dengan lookup koordinat sebenarnya) ---
        # Nanti bisa dihubungkan dengan file koordinat dari BMKG atau Open-Meteo
        lat, lon = -7.379, 112.787  # Sidoarjo sebagai contoh default
        st.write(f"Koordinat perkiraan: {lat}, {lon}")

        # --- Ambil data prakiraan cuaca dari Open-Meteo ---
        url_forecast = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m"
            f"&forecast_days=1&timezone=Asia/Jakarta"
        )

        data = requests.get(url_forecast).json()
        jam = data["hourly"]["time"]
        suhu = data["hourly"]["temperature_2m"]
        hujan = data["hourly"]["precipitation"]
        angin = data["hourly"]["wind_speed_10m"]
        kelembapan = data["hourly"]["relative_humidity_2m"]

        # Ambil nilai tengah (siang hari, jam ke-12)
        suhu_now = suhu[12]
        hujan_now = hujan[12]
        angin_now = angin[12]
        rh_now = kelembapan[12]

        st.subheader("🛰️ Prakiraan Cuaca Hari Ini")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Suhu", f"{suhu_now} °C")
        col2.metric("Curah Hujan", f"{hujan_now} mm")
        col3.metric("Kelembapan", f"{rh_now} %")
        col4.metric("Kecepatan Angin", f"{angin_now} m/s")

        # --- Analisis Dinamika Atmosfer ---
        st.subheader("🌬️ Dinamika Atmosfer yang Mempengaruhi")

        if hujan_now > 5 and angin_now < 5:
            st.info("💧 Hujan lebat diperkirakan terjadi akibat **konvergensi angin** dan kelembapan tinggi di lapisan bawah atmosfer (850–925 hPa).")
        elif hujan_now > 5 and angin_now >= 5:
            st.info("🌧️ Hujan disertai angin kencang, kemungkinan dipicu oleh **shear line** dan konvergensi di lapisan 925 hPa yang memicu konveksi kuat.")
        elif hujan_now > 1 and rh_now > 80:
            st.info("🌤️ Terjadi potensi hujan ringan akibat **pemusatan awan konvektif lokal** dan kondisi lembap di lapisan bawah.")
        elif hujan_now < 1 and rh_now < 60:
            st.info("☀️ Cuaca relatif kering dan stabil, dominan pengaruh **subsiden dari massa udara kering** di lapisan menengah.")
        else:
            st.info("⛅ Kondisi atmosfer relatif stabil tanpa indikasi konvergensi signifikan hari ini.")

        st.caption(f"Data diambil dari Open-Meteo API ({datetime.now().strftime('%d %B %Y %H:%M')} WIB)")
