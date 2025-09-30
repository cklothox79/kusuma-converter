import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Prakiraan Cuaca BMKG – Tahap 2", page_icon="🗺️")
st.title("🗺️ Prakiraan Cuaca BMKG – Tahap 2 (Nama → Koordinat → Peta)")

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
    Contoh panggilan prakiraan cuaca.
    Sementara masih pakai Open-Meteo untuk demonstrasi.
    """
    try:
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

        # --------- Peta Folium ---------
        st.subheader("🗺️ Peta Lokasi")
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
        folium.Marker(
            [lat, lon],
            popup=f"<b>{addr}</b><br>Lat: {lat:.4f}, Lon: {lon:.4f}",
            tooltip="Klik untuk info"
        ).add_to(m)

        # Tampilkan peta di Streamlit
        st_folium(m, width=700, height=450)

        # --------- Data Prakiraan ---------
        st.subheader("🌦️ Prakiraan Cuaca (contoh data Open-Meteo)")
        forecast = get_forecast(lat, lon)

        if forecast:
            hourly = forecast.get("hourly", {})
            if hourly:
                df = pd.DataFrame(hourly)
                st.dataframe(df.head(24))
            else:
                st.warning("Tidak ada data prakiraan pada respons.")
    else:
        st.error("Koordinat tidak ditemukan. Coba nama lain.")
