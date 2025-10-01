# streamlit_app_cuaca_perjalanan.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Cuaca Perjalanan BMKG", layout="wide")
st.title("🌦️ Cuaca Perjalanan – BMKG API")

# ------------------------------
# Load lookup lokasi BIG/BMKG
# ------------------------------
@st.cache_data
def load_lokasi():
    df_lokasi = pd.read_csv("data_lokasi.csv")  # kode,nama,lat,lon
    return df_lokasi

lokasi_df = load_lokasi()

# ------------------------------
# Fungsi bantu
# ------------------------------
def get_forecast_by_coords(lat, lon):
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?lat={lat}&lon={lon}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        return None

def process_forecast_data(raw_data):
    rows = []
    for item in raw_data.get('prakiraan', []):
        rows.append({
            "Tanggal": item['tanggal'],
            "Jam": item['jam'],
            "SuhuMin": item['suhu_min'],
            "SuhuMax": item['suhu_max'],
            "Cuaca": item['cuaca'],
            "CurahHujan(mm)": item['curah_hujan'],
            "Kelembaban(%)": item['kelembaban'],
            "Angin(km/jam)": item['angin']
        })
    return pd.DataFrame(rows)

def generate_warning(df):
    warnings = []
    for i, row in df.iterrows():
        if row['CurahHujan(mm)'] >= 50:
            warnings.append(f"{row['Tanggal']} {row['Jam']}: Hujan lebat!")
        if row['Angin(km/jam)'] >= 20:
            warnings.append(f"{row['Tanggal']} {row['Jam']}: Angin kencang!")
        if row['SuhuMax'] >= 35:
            warnings.append(f"{row['Tanggal']} {row['Jam']}: Suhu sangat panas!")
        if row['SuhuMin'] <= 15:
            warnings.append(f"{row['Tanggal']} {row['Jam']}: Suhu sangat dingin!")
    return warnings

# ------------------------------
# Sidebar Input
# ------------------------------
st.sidebar.header("Pilih Lokasi")
lokasi_input = st.sidebar.text_input("Nama Desa/Kecamatan (opsional)")

lat_input = st.sidebar.number_input("Latitude", value=0.0, format="%.6f")
lon_input = st.sidebar.number_input("Longitude", value=0.0, format="%.6f")

# Jika input nama desa/kecamatan
if lokasi_input:
    row = lokasi_df[lokasi_df['nama'].str.contains(lokasi_input, case=False)]
    if not row.empty:
        lat_input = float(row.iloc[0]['lat'])
        lon_input = float(row.iloc[0]['lon'])
        st.sidebar.success(f"Koordinat otomatis ditemukan: {lat_input}, {lon_input}")
    else:
        st.sidebar.warning("Lokasi tidak ditemukan. Gunakan koordinat manual atau klik peta.")

# ------------------------------
# Peta Interaktif
# ------------------------------
st.subheader("🗺️ Klik peta untuk memilih lokasi")
m = folium.Map(location=[-8.0, 112.6], zoom_start=10)
marker = folium.Marker([lat_input, lon_input], tooltip="Lokasi Terpilih")
marker.add_to(m)

# Tampilkan peta
map_data = st_folium(m, width=700, height=500)

# Update koordinat jika klik peta
if map_data and map_data.get("last_clicked"):
    lat_input = map_data["last_clicked"]["lat"]
    lon_input = map_data["last_clicked"]["lng"]
    st.sidebar.info(f"Koordinat dari klik peta: {lat_input:.6f}, {lon_input:.6f}")

# ------------------------------
# Tombol Ambil Data
# ------------------------------
if st.sidebar.button("Ambil Prakiraan Cuaca"):
    if lat_input == 0.0 and lon_input == 0.0:
        st.error("Masukkan nama lokasi atau klik peta!")
    else:
        st.info("Mengambil data BMKG...")
        data_raw = get_forecast_by_coords(lat_input, lon_input)
        if not data_raw:
            st.error("Gagal mengambil data. Pastikan koordinat valid.")
        else:
            df = process_forecast_data(data_raw)
            
            # Tabel
            st.subheader("📋 Tabel Prakiraan Cuaca")
            st.dataframe(df)
            
            # Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Unduh CSV", data=csv, file_name="prakiraan_cuaca.csv", mime="text/csv")
            
            # Grafik
            st.subheader("📊 Grafik Suhu & Curah Hujan")
            fig_suhu = px.line(df, x="Tanggal", y=["SuhuMin", "SuhuMax"], markers=True, title="Suhu (°C)")
            fig_hujan = px.bar(df, x="Tanggal", y="CurahHujan(mm)", title="Curah Hujan (mm)")
            st.plotly_chart(fig_suhu, use_container_width=True)
            st.plotly_chart(fig_hujan, use_container_width=True)
            
            # Warning
            st.subheader("⚠️ Peringatan Cuaca Buruk")
            warnings = generate_warning(df)
            if warnings:
                for w in warnings:
                    st.warning(w)
            else:
                st.success("Tidak ada cuaca ekstrem terdeteksi.")
