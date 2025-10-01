import streamlit as st
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
from datetime import datetime

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")
st.title("🌦️ Prakiraan Cuaca BMKG")

# --- 1. Load CSV kode wilayah ---
@st.cache_data(ttl=600)
def load_kode_wilayah():
    try:
        df = pd.read_csv("data/kode_wilayah.csv", dtype=str)
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"⚠️ Error load CSV: {e}")
        return pd.DataFrame(columns=['kode','nama'])

kode_df = load_kode_wilayah()

# --- 2. Input lokasi ---
lokasi = st.text_input("Masukkan Nama Desa/Kota", "Simogirang, Sidoarjo")

# --- 3. Geocoding ---
if lokasi:
    try:
        geolocator = Nominatim(user_agent="bmkg-app", timeout=10)
        loc = geolocator.geocode(lokasi)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.write(f"📍 Koordinat: {lat:.5f}, {lon:.5f}")
            st.write(f"🗺️ Alamat: {loc.address}")

            # --- 4. Cari kode wilayah ---
            nama_search = lokasi.split(",")[0].strip().lower()
            match = kode_df[kode_df['nama'].str.lower().str.contains(nama_search)]
            if not match.empty:
                kode = match.iloc[0]['kode']
                st.success(f"Kode Wilayah Ditemukan: {kode}")
            else:
                kode = None
                st.warning("⚠️ Kode wilayah tidak ditemukan di CSV")

            # --- 5. Peta ---
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker([lat, lon], popup=lokasi).add_to(m)
            st_folium(m, width=700, height=500)

            # --- 6. Ambil & tampilkan prakiraan BMKG ---
            if kode:
                try:
                    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
                    r = requests.get(url, timeout=10)

                    if r.ok:
                        data = r.json()
                        st.success("✅ Data BMKG diterima")

                        # --- Parsing data ke tabel ---
                        try:
                            prakiraan = []
                            timeseries = data.get("data", {}).get("cuaca", [])
                            for t in timeseries:
                                jam = datetime.fromisoformat(t.get("datetime")).strftime("%d-%m %H:%M")
                                prakiraan.append({
                                    "🕒 Waktu": jam,
                                    "🌡️ Suhu (°C)": t.get("t", "-"),
                                    "💧 Kelembaban (%)": t.get("hu", "-"),
                                    "🌥️ Cuaca": t.get("weather", "-"),
                                    "🌬️ Angin": f"{t.get('wd', '-')} / {t.get('ws', '-')}"
                                })

                            df_prakiraan = pd.DataFrame(prakiraan)
                            st.subheader("📊 Tabel Prakiraan Cuaca")
                            st.dataframe(df_prakiraan, use_container_width=True)

                        except Exception as e:
                            st.error(f"⚠️ Gagal parsing data BMKG: {e}")
                            st.json(data)

                    else:
                        st.warning("⚠️ Gagal ambil data BMKG, cek endpoint/kode wilayah.")
                        st.info(f"Status code: {r.status_code}")
                except Exception as e:
                    st.warning(f"⚠️ Error saat request BMKG: {e}")
        else:
            st.error("⚠️ Lokasi tidak ditemukan. Coba nama lain.")
    except Exception as e:
        st.error(f"⚠️ Geocoding error: {e}")
