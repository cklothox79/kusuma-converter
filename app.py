import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="🌦️ FUSION PRAKICU 1 HARI – BMKG Style", layout="centered")

st.markdown("## 🌦️ FUSION PRAKICU 1 HARI – BMKG Style")
st.write("Masukkan nama daerah untuk melihat prakiraan cuaca harian yang lebih akurat dan mudah dipahami masyarakat.")
st.divider()

# === Input lokasi ===
lokasi_input = st.text_input("📍 Masukkan nama daerah/desa/kota:", "Simogirang")

# === Contoh database lokal koordinat ===
lokasi_dict = {
    "simogirang": (-7.4899, 112.6583, "Desa Simogirang, Kec. Prambon, Kab. Sidoarjo"),
    "sidoarjo": (-7.4478, 112.7171, "Kabupaten Sidoarjo"),
    "surabaya": (-7.2575, 112.7521, "Kota Surabaya"),
    "malang": (-7.9839, 112.6214, "Kota Malang")
}

lokasi_key = lokasi_input.lower().strip()
if lokasi_key not in lokasi_dict:
    st.warning("⚠️ Lokasi tidak ditemukan di database contoh. Gunakan Simogirang, Surabaya, Malang, atau Sidoarjo untuk demo.")
    st.stop()

lat, lon, nama_lokasi = lokasi_dict[lokasi_key]

# === Ambil data prakiraan Open-Meteo ===
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloudcover,precipitation,weathercode,windspeed_10m&timezone=Asia/Jakarta"
r = requests.get(url)
data = r.json()
df = pd.DataFrame(data["hourly"])
df["time"] = pd.to_datetime(df["time"])

# === Data METAR (opsional) dari OGIMET atau NOAA untuk fusi aktual ===
try:
    metar_url = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/WARR.TXT"
    metar_text = requests.get(metar_url).text
    metar_latest = metar_text.splitlines()[-1]
except Exception:
    metar_latest = "WARR AUTO -- METAR data tidak tersedia"

# === Ambil data untuk hari ini ===
now = datetime.now()
today = now.date()
df_today = df[df["time"].dt.date == today]

def ambil_interval(jam_awal, jam_akhir):
    d = df_today[(df_today["time"].dt.hour >= jam_awal) & (df_today["time"].dt.hour < jam_akhir)]
    return {
        "temp": round(d["temperature_2m"].mean(), 1),
        "rh": round(d["relative_humidity_2m"].mean(), 0),
        "cloud": round(d["cloudcover"].mean(), 0),
        "rain": round(d["precipitation"].sum(), 2),
        "wind": round(d["windspeed_10m"].mean(), 1)
    }

pagi = ambil_interval(6, 12)
siang = ambil_interval(12, 18)
malam = ambil_interval(18, 24)

# === Fungsi deskripsi cuaca (fusion) ===
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
    # modifikasi berdasarkan waktu
    if waktu == "pagi" and "cerah" in teks:
        teks += ", udara terasa sejuk"
    if waktu == "siang" and "cerah" in teks:
        teks += ", suhu terasa panas"
    if waktu == "malam" and "cerah" in teks:
        teks += ", udara mulai terasa dingin"
    return teks

# === Fusi METAR untuk koreksi ===
if "RA" in metar_latest or "SH" in metar_latest or "TS" in metar_latest:
    if siang["rain"] < 1:
        siang["rain"] += 1.5  # koreksi jika METAR mendeteksi hujan
    st.info("💧 Koreksi: Data METAR menunjukkan hujan, prakiraan disesuaikan.")

# === Buat narasi publik ===
narasi = f"""
📍 **{nama_lokasi}**  
🗓️ **{today.strftime('%A, %d %B %Y')}**

🌅 **Pagi hari (06.00–12.00 WIB)** diperkirakan {deskripsi(pagi, "pagi")} dengan suhu sekitar **{pagi['temp']}°C**, kelembaban udara **{pagi['rh']}%**, dan kecepatan angin rata-rata **{pagi['wind']} km/jam**.

☀️ **Siang hari (12.00–18.00 WIB)** kondisi {deskripsi(siang, "siang")} dengan suhu maksimum sekitar **{siang['temp']}°C**, kelembaban **{siang['rh']}%**, dan angin rata-rata **{siang['wind']} km/jam**.

🌙 **Malam hari (18.00–24.00 WIB)** umumnya {deskripsi(malam, "malam")} dengan suhu turun menjadi sekitar **{malam['temp']}°C**, kelembaban **{malam['rh']}%**, dan angin sekitar **{malam['wind']} km/jam**.

💨 Arah angin dominan timur–timur laut dengan kondisi umum **stabil hingga malam hari**.
"""

# === Tampilkan hasil ===
st.success("✅ Prakiraan harian berhasil dibuat!")
st.markdown(narasi)

st.markdown("### 📡 Observasi Terbaru (METAR WARR – Juanda)")
st.code(metar_latest, language="text")

# === Peta lokasi ===
st.markdown("### 🗺️ Lokasi di Peta")
m = folium.Map(location=[lat, lon], zoom_start=11)
folium.Marker([lat, lon], tooltip=nama_lokasi).add_to(m)
st_folium(m, width=700, height=400)
