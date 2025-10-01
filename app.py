import streamlit as st
import pandas as pd
import requests
from geopy.geocoders import Nominatim
import plotly.express as px

st.set_page_config(page_title="Cuaca BMKG", page_icon="🌦️", layout="wide")
st.title("🌦️ Prakiraan Cuaca")

# --- 1. Load CSV kode wilayah ---
@st.cache_data
def load_kode_wilayah():
    df = pd.read_csv("data/kode_wilayah.csv", dtype=str)
    df.columns = [c.lower() for c in df.columns]
    return df

kode_df = load_kode_wilayah()

# --- 2. Input lokasi ---
lokasi = st.text_input("Masukkan Nama Desa, Kecamatan", "Simogirang, Prambon")

if lokasi:
    try:
        # --- 3. Geocoding ---
        geolocator = Nominatim(user_agent="bmkg-app")
        loc = geolocator.geocode(lokasi)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.write(f"📍 Koordinat: {lat:.5f}, {lon:.5f}")
            st.write(f"🗺️ Alamat: {loc.address}")

            # --- 4. Cari kode wilayah di CSV ---
            search_terms = [x.strip().lower() for x in lokasi.split(",")]
            kode = None
            for term in search_terms:
                match = kode_df[kode_df['nama'].str.lower().str.contains(term)]
                if not match.empty:
                    kode = match.iloc[0]['kode']
                    nama_resmi = match.iloc[0]['nama']
                    break

            if kode:
                st.success(f"Kode Wilayah ditemukan: {kode} ({nama_resmi})")
            else:
                st.error("❌ Kode wilayah tidak ditemukan di CSV")
                st.stop()

            # --- 5. Ambil data cuaca BMKG ---
            try:
                url = f"https://api-apps.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
                r = requests.get(url, timeout=10)
                if not r.ok or r.text.strip() == "":
                    st.error("❌ BMKG tidak mengembalikan data")
                    st.stop()
                data = r.json()
                st.success("✅ Data BMKG berhasil diambil")

                # --- 6. Parsing Data Cuaca ---
                cuaca_list = data["data"][0]["cuaca"]
                records = []
                for item in cuaca_list:
                    for c in item:
                        records.append({
                            "datetime": c["local_datetime"],
                            "jam": c["local_datetime"].split(" ")[1][:5],
                            "suhu": c["t"],
                            "kelembapan": c["hu"],
                            "hujan": c["tp"],
                            "deskripsi": c["weather_desc"],
                            "ikon": c["image"],
                            "angin": f'{c["ws"]} km/jam ({c["wd"]})'
                        })
                df = pd.DataFrame(records)

                # === Weather Card ===
                st.subheader("📌 Prakiraan Cuaca per Jam")
                cols = st.columns(3)
                for i, row in df.iterrows():
                    with cols[i % 3]:
                        st.markdown(
                            f"""
                            <div style="border-radius:15px; padding:15px; text-align:center; 
                                        background:#f5f5f5; margin:8px; 
                                        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
                                <h4>{row['jam']}</h4>
                                <img src="{row['ikon']}" width="60">
                                <p><b>{row['suhu']}°C</b></p>
                                <p>{row['deskripsi']}</p>
                                <p>💧 {row['kelembapan']}%</p>
                                <p>🌬️ {row['angin']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                # === Grafik Tren ===
                st.subheader("📊 Tren Cuaca 24 Jam ke Depan")
                tab1, tab2, tab3 = st.tabs(["🌡️ Suhu", "💧 Kelembapan", "🌧️ Hujan"])

                with tab1:
                    fig = px.line(df, x="jam", y="suhu", text="suhu",
                                markers=True, title="Perkiraan Suhu (°C)")
                    fig.update_traces(textposition="top center")
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    fig = px.line(df, x="jam", y="kelembapan", text="kelembapan",
                                markers=True, title="Perkiraan Kelembapan (%)")
                    fig.update_traces(textposition="top center")
                    st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    fig = px.bar(df, x="jam", y="hujan",
                                title="Perkiraan Curah Hujan (mm)")
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"⚠️ Gagal ambil data BMKG: {e}")

        else:
            st.error("❌ Lokasi tidak ditemukan via Geocoding")

    except Exception as e:
        st.error(f"Geocoding error: {e}")
