import streamlit as st
import pandas as pd
import requests
import time
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌍 Geocoding Wilayah Jawa Timur", layout="wide")
st.title("🌍 Tambah Koordinat (Lat-Lon) ke kode_wilayah_jatim.csv")
st.caption("Otomatis isi koordinat dari OpenStreetMap Nominatim — aman, bisa dilanjut jika terputus.")

# =======================================================
# 1️⃣ Load data wilayah (CSV utama dan hasil sebelumnya)
# =======================================================
CSV_PATH = "kode_wilayah_jatim.csv"
OUTPUT_PATH = "kode_wilayah_jatim_with_coords.csv"

@st.cache_data(ttl=3600)
def load_wilayah():
    df = pd.read_csv(CSV_PATH, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

# Baca CSV utama
df = load_wilayah()

# Jika sudah ada hasil sebelumnya, lanjutkan dari sana
if os.path.exists(OUTPUT_PATH):
    st.info("📄 Ditemukan file hasil sebelumnya — akan dilanjutkan dari posisi terakhir.")
    df_existing = pd.read_csv(OUTPUT_PATH, dtype=str)
    if "lat" in df_existing.columns and "lon" in df_existing.columns:
        df = df_existing
else:
    df["lat"] = None
    df["lon"] = None

st.write(f"Jumlah total wilayah: **{len(df)}** baris.")
st.dataframe(df.head())

# =======================================================
# 2️⃣ Fungsi Geocoding
# =======================================================
def geocode_nominatim(name):
    """Ambil koordinat (lat, lon) dari OpenStreetMap Nominatim."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(name)}&format=json&addressdetails=1&limit=1"
        headers = {"User-Agent": "JatimGeocoder/1.0 (cklothoz79.github.io)"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        print(f"Gagal geocoding {name}: {e}")
    return None, None

# =======================================================
# 3️⃣ Proses Geocoding (lanjut dari terakhir)
# =======================================================
if st.button("🚀 Jalankan / Lanjutkan Geocoding"):
    remaining = df[df["lat"].isna() | df["lon"].isna()]
    total_remaining = len(remaining)
    st.write(f"🔍 Masih ada {total_remaining} wilayah tanpa koordinat.")

    if total_remaining == 0:
        st.success("Semua wilayah sudah memiliki koordinat!")
    else:
        progress = st.progress(0)
        start_index = df.index[df["lat"].isna() | df["lon"].isna()]
        total = len(start_index)

        for i, idx in enumerate(start_index):
            row = df.loc[idx]
            full_name = f"{row['nama']}, Jawa Timur, Indonesia"
            lat, lon = geocode_nominatim(full_name)
            df.at[idx, "lat"] = lat
            df.at[idx, "lon"] = lon

            # Simpan progres setiap 10 data
            if i % 10 == 0:
                df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
            progress.progress((i + 1) / total)
            time.sleep(1)

        # Simpan hasil akhir
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        st.success(f"✅ Geocoding selesai! Hasil disimpan di {OUTPUT_PATH}")

        st.download_button(
            "📥 Unduh Hasil CSV Lengkap",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="kode_wilayah_jatim_with_coords.csv",
            mime="text/csv"
        )

# =======================================================
# 4️⃣ Tampilkan Peta Interaktif
# =======================================================
st.subheader("🗺️ Peta Hasil Koordinat")
if "lat" in df.columns and "lon" in df.columns and df["lat"].notna().any():
    valid_points = df.dropna(subset=["lat", "lon"])
    avg_lat = valid_points["lat"].astype(float).mean()
    avg_lon = valid_points["lon"].astype(float).mean()

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7)
    for _, row in valid_points.iterrows():
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            popup=row["nama"]
        ).add_to(m)

    st_folium(m, width=1000, height=600)
else:
    st.info("Belum ada koordinat untuk ditampilkan di peta.")

# =======================================================
# 5️⃣ Catatan Tambahan
# =======================================================
st.markdown("""
---
📝 **Catatan:**
- Proses memerlukan waktu lama (±1 detik per wilayah).
- Data disimpan otomatis di `kode_wilayah_jatim_with_coords.csv` agar bisa **dilanjutkan kapan saja**.
- Jika ada hasil tidak akurat, bisa diperbaiki manual di file CSV akhir.
""")
