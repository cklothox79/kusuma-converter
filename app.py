import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Prakiraan Cuaca BMKG", layout="wide")

# --- 1. Load CSV kode wilayah ---
@st.cache_data
def load_kode_wilayah():
    df = pd.read_csv("data/kode_wilayah.csv", dtype=str)
    df.columns = [c.lower() for c in df.columns]
    return df

kode_df = load_kode_wilayah()

# --- 2. Input lokasi ---
lokasi = st.text_input("Masukkan Nama Desa, Kecamatan", "Simogirang, Prambon")

# --- 3. Cari kode wilayah ---
def cari_kode_wilayah(nama_desa, nama_kec):
    df_match = kode_df[
        (kode_df["nama"].str.lower().str.contains(nama_desa.lower())) &
        (kode_df["nama"].str.lower().str.contains(nama_kec.lower()))
    ]
    if not df_match.empty:
        return df_match.iloc[0]["kode"], df_match.iloc[0]["nama"]
    return None, None

kode, nama_wilayah = None, None
if "," in lokasi:
    desa, kec = [x.strip() for x in lokasi.split(",")]
    kode, nama_wilayah = cari_kode_wilayah(desa, kec)

if kode:
    st.success(f"Kode wilayah ditemukan: {kode} ({nama_wilayah})")

    # --- 4. Ambil data cuaca dari BMKG ---
    try:
        url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            if "data" in data and len(data["data"]) > 0:
                cuaca = data["data"][0]["cuaca"]

                st.subheader(f"🌦️ Prakiraan Cuaca untuk {nama_wilayah}")

                # --- 5. Weather Card ---
                for jam in cuaca[:6]:  # tampilkan 6 waktu terdekat
                    for d in jam:
                        col1, col2, col3 = st.columns([1, 2, 2])
                        with col1:
                            st.image(d["image"], width=60)
                        with col2:
                            st.markdown(
                                f"""
                                **🕒 {d['local_datetime']}**  
                                🌡️ {d['t']}°C | 💧 {d['hu']}%  
                                🌬️ {d['ws']} km/jam ({d['wd']})  
                                """
                            )
                        with col3:
                            st.write(f"**{d['weather_desc']}**")
                        st.divider()
            else:
                st.error("❌ BMKG tidak mengembalikan data prakiraan.")
        else:
            st.error("❌ Gagal ambil data dari BMKG.")
    except Exception as e:
        st.error(f"⚠️ Error ambil data BMKG: {e}")

else:
    st.warning("⚠️ Masukkan format: Desa, Kecamatan. Contoh: `Simogirang, Prambon`")
