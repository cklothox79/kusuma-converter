import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, sqrt, atan2

st.set_page_config(page_title="Prakiraan Cuaca BMKG", page_icon="🌦️", layout="wide")
st.title("🌦️ Prakiraan Cuaca BMKG – Peta & Pencarian Nama")

# ================================
# Fungsi untuk ambil data lokasi
# ================================
@st.cache_data(show_spinner=True)
def get_all_locations(adm1_code="35"):  # 35 = Jawa Timur
    """
    Ambil daftar desa (adm4) lengkap dengan lat/lon di provinsi tertentu.
    adm1_code -> kode provinsi sesuai BMKG (contoh: 35 = Jawa Timur)
    """
    url = f"https://cuaca.bmkg.go.id/api/df/v1/adm/list?adm1={adm1_code}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]
    points = []
    for kab in data:
        for kec in kab.get("children", []):
            for desa in kec.get("children", []):
                points.append({
                    "prov": kab.get("parent_name", "Jawa Timur"),
                    "kab": kab["name"],
                    "kec": kec["name"],
                    "desa": desa["name"],
                    "kode": desa["code"],
                    "lat": desa["lat"],
                    "lon": desa["lon"]
                })
    return points

# ================================
# Fungsi ambil prakiraan
# ================================
def get_forecast(kode_adm4):
    url = f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm?adm4={kode_adm4}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# ================================
# Fungsi cari titik terdekat
# ================================
def nearest_point(points, lat, lon):
    def haversine(p):
        R = 6371  # km
        dlat = radians(p["lat"] - lat)
        dlon = radians(p["lon"] - lon)
        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(p["lat"]))*sin(dlon/2)**2
        return 2 * R * atan2(sqrt(a), sqrt(1-a))
    return min(points, key=haversine)

# ================================
# Ambil data lokasi
# ================================
with st.spinner("🔍 Mengambil daftar wilayah BMKG..."):
    points = get_all_locations()

# ================================
# Sidebar input pencarian
# ================================
st.sidebar.header("🔎 Cari Lokasi")
search_name = st.sidebar.text_input("Nama Desa/Kecamatan/Kota", "")

selected_point = None
if search_name:
    # cari yang mengandung kata kunci (case-insensitive)
    matches = [p for p in points if search_name.lower() in p["desa"].lower()
                                      or search_name.lower() in p["kec"].lower()
                                      or search_name.lower() in p["kab"].lower()]
    if matches:
        selected_point = matches[0]   # ambil yang pertama saja
        st.sidebar.success(
            f"Ditemukan: {selected_point['desa']} - {selected_point['kec']} ({selected_point['kab']})"
        )
    else:
        st.sidebar.warning("Wilayah tidak ditemukan.")

# ================================
# Tampilkan peta
# ================================
if selected_point:
    center = [selected_point["lat"], selected_point["lon"]]
    zoom = 12
else:
    center = [-7.4, 112.7]  # default tengah Jawa Timur
    zoom = 8

m = folium.Map(location=center, zoom_start=zoom)

for p in points:
    # beri warna merah jika hasil pencarian
    color = "red" if selected_point and p["kode"] == selected_point["kode"] else "blue"
    popup_text = (f"<b>{p['desa']}</b><br>{p['kec']} - {p['kab']}<br>Kode: {p['kode']}")
    folium.Marker(
        location=[p["lat"], p["lon"]],
        popup=popup_text,
        tooltip="Klik untuk prakiraan",
        icon=folium.Icon(color=color, icon="cloud")
    ).add_to(m)

map_data = st_folium(m, width=900, height=600)

# ================================
# Jika user klik peta
# ================================
clicked = map_data.get("last_object_clicked")
if clicked:
    lat, lon = clicked["lat"], clicked["lng"]
    sel = nearest_point(points, lat, lon)
    selected_point = sel  # override hasil pencarian jika user klik

# ================================
# Tampilkan prakiraan cuaca
# ================================
if selected_point:
    st.subheader(f"📍 {selected_point['desa']}, {selected_point['kec']} – {selected_point['kab']}")
    st.write(f"Kode wilayah: `{selected_point['kode']}`")
    try:
        with st.spinner("☁️ Mengambil prakiraan cuaca..."):
            forecast = get_forecast(selected_point["kode"])
            if "data" in forecast and forecast["data"]:
                timeseries = forecast["data"][0]["cuaca"]
                st.success("Prakiraan Cuaca:")
                st.table(timeseries)
            else:
                st.warning("Data prakiraan tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal mengambil prakiraan: {e}")
else:
    st.info("💡 Ketik nama desa/kecamatan/kota di sidebar atau klik marker di peta untuk melihat prakiraan.")
