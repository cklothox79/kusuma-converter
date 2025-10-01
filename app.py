# streamlit_app_cuaca_sederhana.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Cuaca Sederhana BMKG", layout="wide")
st.title("🌦️ Prakiraan Cuaca – BMKG (Sederhana)")

# ------------------------------
# Fungsi bantu
# ------------------------------
def get_forecast_by_coords(lat, lon):
    """
    Ambil data BMKG berdasarkan koordinat
    """
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
# Input lokasi (satu kotak teks)
# ------------------------------
lokasi_input = st.text_input("Masukkan Desa/Kecamatan:", "")

# Tombol Ambil Data
if st.button("Ambil Prakiraan Cuaca"):
    if not lokasi_input:
        st.error("Silakan masukkan nama desa/kecamatan!")
    else:
        # Untuk versi simpel ini, kita asumsikan pengguna tahu koordinat
        # atau klik peta bisa ditambahkan nanti. Saat ini pakai input manual.
        # Contoh hardcode untuk demo: Simogirang, Prambon
        lokasi_coords = {
            "Simogirang": (-8.0592, 112.5989),
            # Tambahkan desa lain sesuai kebutuhan
        }

        if lokasi_input in lokasi_coords:
            lat, lon = lokasi_coords[lokasi_input]
            st.info(f"Koordinat otomatis: {lat}, {lon}")
            data_raw = get_forecast_by_coords(lat, lon)

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
        else:
            st.warning("Desa/Kecamatan tidak ada di database demo. Silakan tambahkan koordinatnya.")
