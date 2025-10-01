# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")

st.title("🌦️ Prakiraan Cuaca Interaktif BMKG")

# ------------------------------
# Fungsi bantu
# ------------------------------
def get_forecast_by_coords(lat, lon):
    """
    Mengambil data prakiraan BMKG berdasarkan koordinat
    """
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?lat={lat}&lon={lon}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except:
        return None

def process_forecast_data(raw_data):
    """
    Convert JSON BMKG ke DataFrame standar BIG/BMKG
    """
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
    df = pd.DataFrame(rows)
    return df

def generate_warning(df):
    """
    Deteksi cuaca buruk
    """
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
# Input Lokasi
# ------------------------------
st.sidebar.header("Input Lokasi")
lokasi_input = st.sidebar.text_input("Nama Desa/Kecamatan (opsional)")

lat = st.sidebar.number_input("Latitude", value=0.0, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=0.0, format="%.6f")

if st.sidebar.button("Ambil Prakiraan Cuaca"):
    if lat == 0.0 and lon == 0.0 and not lokasi_input:
        st.error("Masukkan nama lokasi atau koordinat!")
    else:
        st.info("Mengambil data BMKG...")
        data_raw = get_forecast_by_coords(lat, lon)
        if not data_raw:
            st.error("Gagal mengambil data. Pastikan koordinat valid.")
        else:
            df = process_forecast_data(data_raw)
            
            # Tampilkan tabel
            st.subheader("📋 Tabel Prakiraan Cuaca")
            st.dataframe(df)

            # Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Unduh CSV",
                data=csv,
                file_name='prakiraan_cuaca.csv',
                mime='text/csv',
            )

            # Grafik
            st.subheader("📊 Grafik Suhu & Curah Hujan")
            fig = px.line(df, x="Tanggal", y=["SuhuMin", "SuhuMax"], markers=True, title="Suhu (°C)")
            fig2 = px.bar(df, x="Tanggal", y="CurahHujan(mm)", title="Curah Hujan (mm)")
            st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)

            # Warning cuaca buruk
            st.subheader("⚠️ Peringatan Cuaca Buruk")
            warnings = generate_warning(df)
            if warnings:
                for w in warnings:
                    st.warning(w)
            else:
                st.success("Tidak ada cuaca ekstrem terdeteksi.")
