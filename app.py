import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import random

st.set_page_config(page_title="🌦️ Prakiraan Cuaca Harian Jawa Timur", layout="centered")

st.markdown("## 🌦️ Prakiraan Cuaca Harian — Jawa Timur")
st.write("Fusion: Open-Meteo + Geocoding API + Analisis Dinamika Atmosfer (Eksperimental)")
st.divider()

# === Input lokasi ===
lokasi_input = st.text_input("🏙️ Masukkan nama desa/kecamatan/kota di Jawa Timur:", "Simogirang")

# === Fungsi geocoding dengan fallback ke Jawa Timur ===
def cari_lokasi(nama):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={nama}&count=1&language=id&countryCode=ID"
    r = requests.get(url).json()
    if "results" in r and len(r["results"]) > 0:
        return r["results"][0]
    else:
        url2 = f"https://geocoding-api.open-meteo.com/v1/search?name={nama} Jawa Timur&count=1&language=id&countryCode=ID"
        r2 = requests.get(url2).json()
        if "results" in r2 and len(r2["results"]) > 0:
            return r2["results"][0]
        return None

# === Fungsi analisis dinamika atmosfer sederhana ===
def analisis_dinamika(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=u10,v10,relative_humidity_850hPa&forecast_days=1"
        r = requests.get(url).json()

        u = r["hourly"]["u10"]
        v = r["hourly"]["v10"]
        rh850 = r["hourly"].get("relative_humidity_850hPa", [60]*len(u))
        konvergensi = round((sum(abs(u[i]-u[i-1])+abs(v[i]-v[i-1]) for i in range(1, len(u))) / len(u)) / 10, 2)
        kelembapan = round(sum(rh850)/len(rh850), 1)

        if konvergensi > 0.5 and kelembapan > 75:
            return "Terdapat pertemuan massa udara (konvergensi) di sekitar wilayah ini dengan kelembapan tinggi, sehingga potensi hujan meningkat."
        elif konvergensi > 0.3:
            return "Angin di wilayah ini menunjukkan pertemuan lemah, dengan peluang hujan lokal terutama pada siang hingga sore hari."
        else:
            return "Tidak terdapat indikasi konvergensi signifikan, cuaca cenderung stabil dengan peluang hujan rendah."
    except:
        return "Data dinamika atmosfer tidak dapat diambil saat ini."

# === Ambil lokasi ===
lokasi_data = cari_lokasi(lokasi_input)
if not lokasi_data:
    st.warning("⚠️ Lokasi tidak ditemukan. Coba tambahkan nama kabupaten atau kota, misalnya 'Simogirang Sidoarjo'.")
    st.stop()

lat = lokasi_data["latitude"]
lon = lokasi_data["longitude"]
nama_lokasi = lokasi_data["name"] + ", " + lokasi_data.get("admin1", "Jawa Timur")

# === Ambil data cuaca dari Open-Meteo ===
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation_probability&forecast_days=1&timezone=Asia%2FJakarta"
r = requests.get(url).json()

df = pd.DataFrame(r["hourly"])
df["time"] = pd.to_datetime(df["time"])
df["hour"] = df["time"].dt.hour

# === Bagi waktu pagi/siang/sore/malam ===
def ringkas_cuaca(jam_awal, jam_akhir):
    d = df[(df["hour"]>=jam_awal) & (df["hour"]<jam_akhir)]
    suhu = round(d["temperature_2m"].mean(),1)
    rh = round(d["relative_humidity_2m"].mean(),1)
    pop = round(d["precipitation_probability"].mean(),1)
    return suhu, rh, pop

pagi = ringkas_cuaca(6, 10)
siang = ringkas_cuaca(10, 15)
sore = ringkas_cuaca(15, 18)
malam = ringkas_cuaca(18, 24)

# === Analisis dinamika atmosfer ===
dinamika = analisis_dinamika(lat, lon)

# === Narasi publik ===
narasi = f"""
🌤️ **Prakiraan Cuaca Harian untuk {nama_lokasi}**

- **Pagi hari:** Cuaca umumnya cerah berawan dengan suhu sekitar **{pagi[0]}°C** dan kelembapan **{pagi[1]}%**. Peluang hujan sekitar **{pagi[2]}%**.  
- **Siang hari:** Udara terasa lebih hangat (**{siang[0]}°C**) dengan potensi hujan **{siang[2]}%**, terutama bila terbentuk awan konvektif lokal.  
- **Sore hari:** Kondisi cenderung **{'berpotensi hujan' if sore[2]>40 else 'cerah berawan'}**, suhu rata-rata **{sore[0]}°C**.  
- **Malam hari:** Suhu menurun ke sekitar **{malam[0]}°C**, udara terasa lembap (**{malam[1]}%**) dengan potensi hujan **{malam[2]}%**.

🌬️ **Analisis Dinamika Atmosfer:**  
{dinamika}
"""

# === Tampilkan hasil ===
st.success("✅ Prakiraan berhasil dibuat!")
st.markdown(narasi)
st.map(pd.DataFrame({"lat":[lat], "lon":[lon]}), zoom=9)

st.caption("Sumber data: Open-Meteo API (ECMWF + GFS Fusion) | Analisis oleh Kusuma Converter v2")
