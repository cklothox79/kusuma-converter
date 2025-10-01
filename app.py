import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌦️ Prakiraan Cuaca Interaktif BMKG", layout="wide")

st.title("🌦️ Prakiraan Cuaca Interaktif BMKG")

# ------------------------
# Fungsi ambil data BMKG
# ------------------------
def get_forecast_by_name(query):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?nama={query}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return None
    except Exception as e:
        return None

def get_forecast_by_latlon(lat, lon):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?lat={lat}&lon={lon}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return None
    except Exception as e:
        return None

# ------------------------
# Layout dua kolom
# ------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 Input Manual")
    lokasi_input = st.text_input("Masukkan Nama Desa, Kecamatan", "Simogirang, Prambon")

    forecast_data = None
    if lokasi_input:
        data = get_forecast_by_name(lokasi_input)
        if data and "lokasi" in data:
            kode = data["lokasi"]["adm4"]
            st.success(f"✅ Ditemukan kode wilayah: {kode} ({data['lokasi'].get('desa','')})")
            forecast_data = data
        else:
            st.error("❌ Lokasi tidak ditemukan. Coba nama lain.")

with col2:
    st.subheader("🗺️ Klik Peta")

    # Peta awal di Jawa Timur
    m = folium.Map(location=[-7.5, 112.5], zoom_start=8)
    st_map = st_folium(m, height=400, width=500)

    if st_map and st_map.get("last_clicked"):
        lat = st_map["last_clicked"]["lat"]
        lon = st_map["last_clicked"]["lng"]
        st.write(f"📍 Koordinat dipilih: {lat:.4f}, {lon:.4f}")

        data = get_forecast_by_latlon(lat, lon)
        if data and "lokasi" in data:
            kode = data["lokasi"]["adm4"]
            desa = data["lokasi"].get("desa", "")
            kec = data["lokasi"].get("kecamatan", "")
            st.success(f"✅ Ditemukan kode wilayah dari peta: {kode} ({desa}, {kec})")

            # Auto update input manual
            st.session_state["lokasi_input"] = f"{desa}, {kec}"
            forecast_data = data
        else:
            st.error("❌ Tidak ada data untuk lokasi ini.")

# ------------------------
# Tampilkan prakiraan cuaca
# ------------------------
if forecast_data:
    st.subheader(f"🌦️ Prakiraan Cuaca untuk {forecast_data['lokasi'].get('desa','')}")
    cuaca = forecast_data["data"][0]["cuaca"]
    for blok in cuaca:
        for item in blok:
            waktu = item["local_datetime"]
            suhu = item["t"]
            kondisi = item["weather_desc"]
            icon = item["image"]

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;margin:5px 0;padding:5px;border:1px solid #ddd;border-radius:8px;">
                    <img src="{icon}" width="40" style="margin-right:10px"/>
                    <div>
                        <b>{waktu}</b><br>
                        🌡️ {suhu}°C | {kondisi}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
