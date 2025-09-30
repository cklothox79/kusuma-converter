import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")
st.title("🌦️ Prakiraan Cuaca BMKG – Peta & Nama Daerah")

# -----------------------------
# 1️⃣  Inisialisasi Session State
# -----------------------------
if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.nama = None

# -----------------------------
# 2️⃣  Input Nama Lokasi
# -----------------------------
geolocator = Nominatim(user_agent="bmkg_app", timeout=15)
lokasi_input = st.sidebar.text_input("Masukkan nama daerah (desa/kota/kecamatan):", "")
tombol_cari = st.sidebar.button("🔍 Cari Lokasi")

if tombol_cari and lokasi_input:
    with st.spinner("🔎 Mencari koordinat lokasi..."):
        try:
            lokasi = geolocator.geocode(f"{lokasi_input}, Indonesia")
            if lokasi:
                st.session_state.lat = lokasi.latitude
                st.session_state.lon = lokasi.longitude
                st.session_state.nama = lokasi.address
                st.sidebar.success(f"Lokasi ditemukan: {lokasi.address}")
            else:
                st.sidebar.error("Lokasi tidak ditemukan, coba nama lain.")
        except Exception as e:
            st.sidebar.error(f"Error geocoding: {e}")

latitude = st.session_state.lat
longitude = st.session_state.lon
nama_lokasi = st.session_state.nama

# -----------------------------
# 3️⃣  Peta Dasar
# -----------------------------
m = folium.Map(location=[-7.5, 112.7], zoom_start=7)
if latitude and longitude:
    folium.Marker([latitude, longitude],
                  popup=nama_lokasi,
                  tooltip="Lokasi Anda").add_to(m)
st_data = st_folium(m, width=900, height=500)

# -----------------------------
# 4️⃣  Tampilkan Koordinat
# -----------------------------
if latitude and longitude:
    st.success(
        f"📍 **Koordinat**: {latitude:.5f}, {longitude:.5f}\n\n"
        f"🗺️ **Alamat**: {nama_lokasi}"
    )

# -----------------------------
# 5️⃣  Ambil Kode Wilayah BMKG
# -----------------------------
def get_bmkg_code(lat, lon):
    try:
        lokasi = geolocator.reverse((lat, lon), language="id", timeout=15)
        if not lokasi:
            return None, None, None, None, None

        alamat = lokasi.raw.get("address", {})
        prov = alamat.get("state", "")
        kab = alamat.get("county", "")
        kec = (
            alamat.get("suburb", "")
            or alamat.get("village", "")
            or alamat.get("city_district", "")
        )
        desa = alamat.get("hamlet", "") or alamat.get("village", "")

        base = "https://cuaca.bmkg.go.id/api/df/v1/adm"

        # --- adm1 (Provinsi)
        r1 = requests.get(f"{base}/list")
        r1.raise_for_status()
        prov_list = r1.json()["data"]
        adm1 = next((p["adm1"] for p in prov_list
                     if prov.lower().startswith(p["name"].lower())), None)

        if not adm1:
            return None, prov, kab, kec, desa

        # --- adm2 (Kab/Kota)
        r2 = requests.get(f"{base}/list?adm1={adm1}")
        r2.raise_for_status()
        kab_list = r2.json()["data"]
        adm2 = next((k["adm2"] for k in kab_list
                     if kab.lower().startswith(k["name"].lower())), None)

        if not adm2:
            return adm1, prov, kab, kec, desa

        # --- adm3 (Kecamatan)
        r3 = requests.get(f"{base}/list?adm1={adm1}&adm2={adm2}")
        r3.raise_for_status()
        kec_list = r3.json()["data"]
        adm3 = next((kc["adm3"] for kc in kec_list
                     if kec.lower().startswith(kc["name"].lower())), None)

        # --- adm4 (Desa/Kelurahan)
        adm4 = None
        if adm3:
            r4 = requests.get(f"{base}/list?adm1={adm1}&adm2={adm2}&adm3={adm3}")
            r4.raise_for_status()
            desa_list = r4.json()["data"]
            adm4 = next((d["adm4"] for d in desa_list
                         if desa.lower().startswith(d["name"].lower())), None)

        return adm1, adm2, adm3, adm4, prov
    except Exception as e:
        st.error(f"❌ Gagal ambil kode BMKG: {e}")
        return None, None, None, None, None

if latitude and longitude:
    with st.spinner("🔎 Mencari kode wilayah BMKG..."):
        adm1, adm2, adm3, adm4, prov = get_bmkg_code(latitude, longitude)

    if adm1:
        st.success(
            f"**Kode BMKG**\n"
            f"- Provinsi (adm1): `{adm1}`\n"
            f"- Kab/Kota (adm2): `{adm2}`\n"
            f"- Kecamatan (adm3): `{adm3}`\n"
            f"- Desa/Kelurahan (adm4): `{adm4}`"
        )
    else:
        st.warning("⚠️ Kode BMKG belum ditemukan. Coba lokasi lain.")

# -----------------------------
# 6️⃣  Ambil Prakiraan Cuaca
# -----------------------------
def get_forecast(adm1, adm2, adm3, adm4):
    try:
        url = (
            f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
            f"?adm1={adm1}&adm2={adm2}&adm3={adm3}&adm4={adm4}"
        )
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ Gagal mengambil prakiraan: {e}")
        return None

if latitude and longitude and adm1 and adm2 and adm3 and adm4:
    with st.spinner("☁️ Mengambil prakiraan cuaca..."):
        forecast = get_forecast(adm1, adm2, adm3, adm4)

    if forecast:
        st.subheader("🔮 Prakiraan Cuaca BMKG")
        for item in forecast.get("data", []):
            jam = item.get("local_datetime", "")
            cuaca = item.get("weather_desc", "")
            suhu = item.get("t", "")
            st.write(f"📅 {jam} | 🌦️ {cuaca} | 🌡️ {suhu}°C")
