import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="🌦️ FUSION PRAKICU PUBLIK – BMKG Style", layout="centered")

st.markdown("## 🌦️ FUSION PRAKICU PUBLIK – BMKG Style")
st.write("Masukkan nama daerah atau desa untuk melihat prakiraan cuaca yang mudah dipahami masyarakat umum.")
st.divider()

# === Input lokasi ===
lokasi_input = st.text_input("📍 Masukkan nama daerah/desa/kota:", "Simogirang")

# === Contoh lookup sederhana ===
lokasi_dict = {
    "simogirang": (-7.4899, 112.6583, "Desa Simogirang, Kec. Prambon, Kab. Sidoarjo"),
    "surabaya": (-7.2575, 112.7521, "Kota Surabaya"),
    "malang": (-7.9839, 112.6214, "Kota Malang"),
    "sidoarjo": (-7.4478, 112.7171, "Kabupaten Sidoarjo")
}

lokasi_key = lokasi_input.lower().strip()
if lokasi_key in lokasi_dict:
    lat, lon, nama_lokasi = lokasi_dict[lokasi_key]
else:
    st.warning("⚠️ Lokasi tidak ditemukan di database contoh. Gunakan Simogirang, Surabaya, Malang, atau Sidoarjo untuk demo.")
    st.stop()

# === Ambil data prakiraan Open-Meteo ===
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloudcover,precipitation,weathercode,windspeed_10m&timezone=Asia/Jakarta"
r = requests.get(url)
data = r.json()

df = pd.DataFrame(data["hourly"])
df["time"] = pd.to_datetime(df["time"])

# Ambil waktu lokal sekarang
now = datetime.now()

# === Filter data hari ini ===
today = now.date()
df_today = df[df["time"].dt.date == today]

if df_today.empty:
    st.error("Data prakiraan belum tersedia untuk hari ini.")
    st.stop()

# === Kelompok waktu ===
def ambil_rata2(waktu_mulai, waktu_akhir):
    d = df_today[(df_today["time"].dt.hour >= waktu_mulai) & (df_today["time"].dt.hour < waktu_akhir)]
    return {
        "temp": d["temperature_2m"].mean(),
        "rh": d["relative_humidity_2m"].mean(),
        "cloud": d["cloudcover"].mean(),
        "rain": d["precipitation"].sum(),
        "wind": d["windspeed_10m"].mean()
    }

pagi = ambil_rata2(6, 12)
siang = ambil_rata2(12, 18)
malam = ambil_rata2(18, 24)

# === Fungsi deskripsi otomatis ===
def deskripsi_cuaca(avg):
    if avg["rain"] > 2:
        return "berpotensi hujan sedang hingga lebat"
    elif avg["rain"] > 0.2:
        return "berpotensi hujan ringan"
    elif avg["cloud"] > 70:
        return "berawan tebal"
    elif avg["cloud"] > 40:
        return "cerah berawan"
    else:
        return "cerah"

# === Buat narasi otomatis ===
narasi = f"""
📍 **{nama_lokasi}**  
🗓️ **{today.strftime('%A, %d %B %Y')}**

🌅 **Pagi hari (06.00–12.00 WIB)** diperkirakan {deskripsi_cuaca(pagi)} dengan suhu sekitar **{pagi['temp']:.1f}°C** dan kelembaban udara **{pagi['rh']:.0f}%**.

☀️ **Siang hari (12.00–18.00 WIB)** kondisi {deskripsi_cuaca(siang)}, suhu udara meningkat hingga sekitar **{siang['temp']:.1f}°C**, dengan kelembaban **{siang['rh']:.0f}%**.

🌙 **Malam hari (18.00–24.00 WIB)** umumnya {deskripsi_cuaca(malam)} dengan suhu turun menjadi sekitar **{malam['temp']:.1f}°C** dan kelembaban **{malam['rh']:.0f}%**.

💨 Angin dominan dengan kecepatan rata-rata **{(pagi['wind']+siang['wind']+malam['wind'])/3:.1f} km/jam**.
"""

st.success("✅ Prakiraan cuaca berhasil diambil!")
st.markdown(narasi)

# === Peta lokasi ===
st.markdown("### 🗺️ Lokasi di Peta")
m = folium.Map(location=[lat, lon], zoom_start=11)
folium.Marker([lat, lon], tooltip=nama_lokasi).add_to(m)
st_folium(m, width=700, height=400)
