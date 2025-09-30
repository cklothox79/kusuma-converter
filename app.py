import streamlit as st
import requests
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Prakiraan Cuaca BMKG – Tahap 1", page_icon="🌦️")
st.title("🌦️ Prakiraan Cuaca BMKG – Tahap 1 (Nama → Koordinat → Prakiraan)")

# =========================
# Fungsi bantu
# =========================
def geocode_place(place_name):
    """Mengubah nama daerah menjadi koordinat lat, lon"""
    geolocator = Nominatim(user_agent="bmkg_geocode")
    location = geolocator.geocode(place_name + ", Indonesia")
    if location:
        return location.latitude, location.longitude, location.address
    return None, None, None

def get_forecast(lat, lon):
    """
    Contoh panggilan prakiraan BMKG berbasis koordinat.
    Catatan: BMKG resmi pakai kode adm.
    Di sini kita coba endpoint 'forecast/point' bila tersedia.
    """
    # Jika endpoint point tidak ada, bisa diarahkan ke adm
    # atau gunakan web scraping. Untuk contoh, kita gunakan endpoint adm terdekat.
    # Di bawah adalah contoh *dummy fallback* agar tetap jalan.
    try:
        # --- Ganti jika ada endpoint BMKG untuk lat/lon ---
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Gagal mengambil prakiraan: {e}")
        return None

# =========================
# Input user
# =========================
place = st.text_input("Masukkan nama desa/kota (contoh: Simogirang, Sidoarjo, Malang):")

if place:
    st.write(f"🔍 Mencari koordinat untuk **{place}** ...")
    lat, lon, addr = geocode_place(place)

    if lat and lon:
        st.success(f"📍 Koordinat ditemukan: {addr}\nLat: {lat:.4f}, Lon: {lon:.4f}")

        st.write("🔎 Mengambil prakiraan cuaca (contoh data Open-Meteo, sementara) ...")
        forecast = get_forecast(lat, lon)

        if forecast:
            # tampilkan ringkasan
            hourly = forecast.get("hourly", {})
            if hourly:
                import pandas as pd
                df = pd.DataFrame(hourly)
                st.dataframe(df.head(24))  # tampil 24 jam ke depan
            else:
                st.warning("Tidak ada data prakiraan pada respons.")
    else:
        st.error("Koordinat tidak ditemukan. Coba nama lain.")
