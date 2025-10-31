import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="🌦️ FUSION PRAKICU 1 HARI – Jawa Timur", layout="centered")

st.markdown("## 🌦️ FUSION PRAKICU 1 HARI – Jawa Timur")
st.write("Masukkan nama daerah atau gunakan lokasi otomatis untuk melihat prakiraan cuaca harian yang mudah dipahami masyarakat.")
st.divider()

# === Opsi deteksi lokasi otomatis ===
use_gps = st.checkbox("📍 Deteksi lokasi otomatis (gunakan GPS browser)", value=False)

if use_gps:
    # fitur ini memerlukan pengaturan tambahan di Streamlit (javascript) – sebagai placeholder:
    st.write("🔧 Fitur GPS belum di-aktifkan sepenuhnya. Silakan ketik nama lokasi sebagai alternatif.")
    lokasi_input = st.text_input("📍 Masukkan nama daerah/desa/kota:", "Simogirang")
else:
    lokasi_input = st.text_input("📍 Masukkan nama daerah/desa/kota:", "Simogirang")

# === Lookup koordinat dengan geocoding API dari Open-Meteo ===
geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={lokasi_input}&count=1&language=id&countryCode=ID"
geo_r = requests.get(geo_url).json()
if "results" in geo_r and len(geo_r["results"])>0:
    lat = geo_r["results"][0]["latitude"]
    lon = geo_r["results"][0]["longitude"]
    nama_lokasi = geo_r["results"][0]["name"] + (", " + geo_r["results"][0]["admin1"] if "admin1" in geo_r["results"][0] else "")
else:
    st.warning("⚠️ Lokasi tidak ditemukan. Silakan periksa ejaan atau ketik nama kabupaten/kota di Jawa Timur.")
    st.stop()

# === Ambil data prakiraan dari Open-Meteo (dukungan global) ===
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloudcover,precipitation,windspeed_10m&timezone=Asia/Jakarta"
r = requests.get(url)
data = r.json()
if "hourly" not in data:
    st.error("❌ Data cuaca tidak tersedia untuk lokasi ini.")
    st.stop()

df = pd.DataFrame(data["hourly"])
df["time"] = pd.to_datetime(df["time"])

# === Filter data hari ini ===
now = datetime.now()
today = now.date()
df_today = df[df["time"].dt.date == today]
if df_today.empty:
    st.error("Data prakiraan belum tersedia untuk hari ini.")
    st.stop()

# === Fungsi ambil rata² interval waktu ===
def ambil_interval(jam_awal, jam_akhir):
    d = df_today[(df_today["time"].dt.hour >= jam_awal) & (df_today["time"].dt.hour < jam_akhir)]
    return {
        "temp": round(d["temperature_2m"].mean(), 1),
        "rh": round(d["relative_humidity_2m"].mean(), 0),
        "cloud": round(d["cloudcover"].mean(), 0),
        "rain": round(d["precipitation"].sum(), 2),
        "wind": round(d["windspeed_10m"].mean(), 1)
    }

pagi  = ambil_interval(6, 12)
siang = ambil_interval(12, 18)
malam = ambil_interval(18, 24)

# === Deskripsi cuaca otomatis ===
def deskripsi(avg, waktu):
    rain = avg["rain"]
    cloud = avg["cloud"]
    if rain > 5:
        teks = "hujan sedang hingga lebat"
    elif rain > 1:
        teks = "berpotensi hujan ringan"
    elif cloud > 70:
        teks = "berawan tebal"
    elif cloud > 40:
        teks = "cerah berawan"
    else:
        teks = "cerah"
    if waktu == "pagi" and "cerah" in teks:
        teks += ", udara terasa sejuk"
    if waktu == "siang" and "cerah" in teks:
        teks += ", suhu terasa panas"
    if waktu == "malam" and "cerah" in teks:
        teks += ", udara mulai terasa dingin"
    return teks

# === Narasi publik ===
narasi = f"""
📍 **{nama_lokasi}**  
🗓️ **{today.strftime('%A, %d %B %Y')}**

🌅 **Pagi hari (06.00–12.00 WIB)** diperkirakan {deskripsi(pagi, "pagi")} dengan suhu sekitar **{pagi['temp']}°C**, kelembaban udara **{pagi['rh']}%**, dan angin rata-rata **{pagi['wind']} km/jam**.

☀️ **Siang hari (12.00–18.00 WIB)** kondisi {deskripsi(siang, "siang")} dengan suhu maksimum sekitar **{siang['temp']}°C**, kelembaban **{siang['rh']}%**, dan angin rata-rata **{siang['wind']} km/jam**.

🌙 **Malam hari (18.00–24.00 WIB)** umumnya {deskripsi(malam, "malam")} dengan suhu turun menjadi sekitar **{malam['temp']}°C**, kelembaban **{malam['rh']}%**, dan angin sekitar **{malam['wind']} km/jam**.

💨 Arah angin dominan dan kondisi umum stabil hingga malam hari.
"""

st.success("✅ Prakiraan harian berhasil dibuat!")
st.markdown(narasi)

# === Tampilkan grafik per jam suhu & curah hujan ===
st.markdown("### 📊 Grafik suhu & curah hujan sepanjang hari")
import plotly.express as px
fig = px.line(df_today, x="time", y=["temperature_2m","precipitation"], labels={"value":"Nilai","time":"Waktu"}, title="Suhu (°C) & Curah Hujan (mm) per Jam")
st.plotly_chart(fig, use_container_width=True)

# === Peta lokasi ===
st.markdown("### 🗺️ Lokasi pada peta")
m = folium.Map(location=[lat, lon], zoom_start=10)
folium.Marker([lat, lon], tooltip=nama_lokasi).add_to(m)
st_folium(m, width=700, height=400)
