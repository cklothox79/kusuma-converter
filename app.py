import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- Fungsi ambil data BMKG ---
def get_bmkg_weather(adm4_code):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4_code}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# --- Mapping cuaca ke icon ---
def get_weather_icon(desc):
    mapping = {
        "Cerah": "https://api-apps.bmkg.go.id/storage/icon/cuaca/cerah-am.svg",
        "Cerah Berawan": "https://api-apps.bmkg.go.id/storage/icon/cuaca/cerah-berawan-am.svg",
        "Berawan": "https://api-apps.bmkg.go.id/storage/icon/cuaca/berawan-am.svg",
        "Hujan Ringan": "https://api-apps.bmkg.go.id/storage/icon/cuaca/hujan-ringan-am.svg",
        "Hujan Sedang": "https://api-apps.bmkg.go.id/storage/icon/cuaca/hujan-sedang-am.svg",
        "Hujan Lebat": "https://api-apps.bmkg.go.id/storage/icon/cuaca/hujan-lebat-am.svg",
    }
    return mapping.get(desc, mapping["Berawan"])

# --- Input Lokasi ---
st.title("🌦️ Peta Prakiraan Cuaca BMKG (Sliding)")

desa = st.text_input("Masukkan Nama Desa:")
kecamatan = st.text_input("Masukkan Nama Kecamatan:")

if desa and kecamatan:
    lokasi = f"{desa},{kecamatan}"
    st.write(f"📍 Lokasi: **{lokasi}**")

    # Hardcode contoh: Simogirang
    kode_adm4 = "35.15.02.2018"

    data = get_bmkg_weather(kode_adm4)

    if not data:
        st.error("❌ BMKG tidak mengembalikan data")
    else:
        lokasi_info = data.get("lokasi", {})
        cuaca_data = data.get("data", [])[0].get("cuaca", [])[0]

        lat = lokasi_info.get("lat", -7.44)
        lon = lokasi_info.get("lon", 112.58)

        # --- Slider waktu ---
        times = [item.get("local_datetime", "").split(" ")[1][:5] for item in cuaca_data]
        time_labels = [t + " WIB" for t in times]

        idx = st.slider("Pilih Waktu Prakiraan", 0, len(time_labels)-1, 0, format="%d")
        current = cuaca_data[idx]

        jam = time_labels[idx]
        suhu = current.get("t", "-")
        hu = current.get("hu", "-")
        desc = current.get("weather_desc", "-")
        icon_url = get_weather_icon(desc)

        # --- Buat Peta ---
        m = folium.Map(location=[lat, lon], zoom_start=13)

        popup_html = f"""
        <b>Jam:</b> {jam}<br>
        <b>Cuaca:</b> {desc}<br>
        <b>Suhu:</b> {suhu}°C<br>
        <b>Kelembaban:</b> {hu}%
        """

        folium.Marker(
            [lat, lon],
            tooltip=f"{jam} - {desc}",
            popup=popup_html,
            icon=folium.CustomIcon(icon_url, icon_size=(60, 60))
        ).add_to(m)

        # Tampilkan peta
        st_folium(m, width=700, height=500)

        # --- Detail di bawah peta ---
        st.subheader("📊 Detail Prakiraan")
        st.write(f"**Jam:** {jam}")
        st.write(f"**Cuaca:** {desc}")
        st.write(f"**Suhu:** {suhu} °C")
        st.write(f"**Kelembaban:** {hu}%")

else:
    st.info("Masukkan format: Desa, Kecamatan. Contoh: `Simogirang, Prambon`")
