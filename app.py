import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime
from pathlib import Path

# -----------------------------
# 1️⃣  Load daftar wilayah
# -----------------------------
csv_path = Path("data/kode_wilayah.csv")
df_wilayah = pd.read_csv(csv_path)

st.title("🌦️ Prakiraan Cuaca – BMKG")

# Pilih wilayah
prov = st.selectbox("Pilih Provinsi", sorted(df_wilayah['provinsi'].unique()))
kab  = st.selectbox("Pilih Kabupaten/Kota",
                    sorted(df_wilayah[df_wilayah['provinsi']==prov]['kabupaten/kota'].unique()))
kec  = st.selectbox("Pilih Kecamatan",
                    sorted(df_wilayah[(df_wilayah['provinsi']==prov)&
                                      (df_wilayah['kabupaten/kota']==kab)]['kecamatan'].unique()))
desa = st.selectbox("Pilih Desa/Kelurahan",
                    sorted(df_wilayah[(df_wilayah['provinsi']==prov)&
                                      (df_wilayah['kabupaten/kota']==kab)&
                                      (df_wilayah['kecamatan']==kec)]['desa'].unique()))

kode = df_wilayah[(df_wilayah['provinsi']==prov)&
                  (df_wilayah['kabupaten/kota']==kab)&
                  (df_wilayah['kecamatan']==kec)&
                  (df_wilayah['desa']==desa)]['kode'].values[0]

st.info(f"Kode BMKG: **{kode}**")

# -----------------------------
# 2️⃣  Ambil Data BMKG
# -----------------------------
url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}"
@st.cache_data(ttl=3600)
def get_bmkg(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()
try:
    data = get_bmkg(url)
except Exception as e:
    st.error(f"Gagal mengambil data BMKG: {e}")
    st.stop()

# -----------------------------
# 3️⃣  Ekstrak Data Jam-per-Jam
# -----------------------------
def parse_bmkg(jsondata):
    rows = []
    cuaca = jsondata['data'][0]['cuaca']
    for c in cuaca:
        waktu = datetime.fromisoformat(c['local_datetime']).strftime('%Y-%m-%d %H:%M')
        rows.append({
            "Waktu": waktu,
            "Suhu (°C)": c['t'],
            "Kelembapan (%)": c['hu'],
            "Hujan (mm)": c['rr'],
            "Cuaca": c['weather'],
            "Ikon": c['icon']
        })
    return pd.DataFrame(rows)

df_cuaca = parse_bmkg(data)

# -----------------------------
# 4️⃣  Pilih Tanggal
# -----------------------------
tanggal_unik = sorted(df_cuaca['Waktu'].str[:10].unique())
tgl_pilih = st.selectbox("Pilih Tanggal", tanggal_unik)
df_hari = df_cuaca[df_cuaca['Waktu'].str.startswith(tgl_pilih)]

# -----------------------------
# 5️⃣  Tabel Prakiraan
# -----------------------------
st.subheader("📋 Tabel Prakiraan Per Jam")
st.dataframe(df_hari, hide_index=True)

# -----------------------------
# 6️⃣  Grafik Suhu
# -----------------------------
st.subheader("📈 Grafik Suhu (°C)")
fig_t = px.line(df_hari, x="Waktu", y="Suhu (°C)", markers=True)
st.plotly_chart(fig_t, use_container_width=True)

# -----------------------------
# 7️⃣  Grafik Curah Hujan
# -----------------------------
st.subheader("💧 Grafik Curah Hujan (mm)")
fig_r = px.bar(df_hari, x="Waktu", y="Hujan (mm)")
st.plotly_chart(fig_r, use_container_width=True)
