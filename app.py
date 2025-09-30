import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", layout="wide")

# =======================
# 1. Fungsi Ambil Data
# =======================
@st.cache_data(show_spinner=False)
def get_all_locations():
    """
    Mengambil seluruh daftar wilayah hingga level desa dari API BMKG
    untuk ditampilkan di peta.
    """
    url = "https://cuaca.bmkg.go.id/api/df/v1/adm/all"  # ✅ Endpoint publik BMKG
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    raw = r.json()

    # Gabungkan semua level menjadi dataframe dengan koordinat
    records = []
    for p in raw["data"]:
        # Pastikan setiap record punya lat/lon
        if p.get("lat") and p.get("lon"):
            records.append({
                "Provinsi": p.get("adm1_name"),
                "Kab/Kota": p.get("adm2_name"),
                "Kecamatan": p.get("adm3_name"),
                "Desa": p.get("adm4_name"),
                "adm1": p.get("adm1"),
                "adm2": p.get("adm2"),
                "adm3": p.get("adm3"),
                "adm4": p.get("adm4"),
                "lat": float(p["lat"]),
                "lon": float(p["lon"])
            })
    return pd.DataFrame(records)

@st.cache_data(show_spinner=False)
def get_forecast(adm1, adm2, adm3, adm4):
    """Ambil prakiraan cuaca dari BMKG berdasarkan kode wilayah."""
    url = (
        f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm?"
        f"adm1={adm1}&adm2={adm2}&adm3={adm3}&adm4={adm4}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# =======================
# 2. Ambil Data Wilayah
# =======================
st.title("🌦️ Prakiraan Cuaca BMKG – Peta & Pencarian Nama")

with st.spinner("🔍 Mengambil daftar lokasi dari BMKG..."):
    try:
        df = get_all_locations()
    except Exception as e:
        st.error(f"Gagal memuat daftar lokasi BMKG: {e}")
        st.stop()

# =======================
# 3. Input Nama Daerah
# =======================
col1, col2 = st.columns([1,2])
with col1:
    query = st.text_input(
        "🔎 Masukkan nama daerah (Desa/Kecamatan/Kota/Provinsi)",
        placeholder="Contoh: Simogirang"
    )

# Filter berdasarkan input user
filtered = df
if query:
    filtered = df[df.apply(lambda x: query.lower() in " ".join(x.astype(str)).lower(), axis=1)]

with col1:
    st.write(f"🔹 Ditemukan **{len(filtered)}** lokasi")

# =======================
# 4. Tampilkan Peta
# =======================
layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered,
    get_position=["lon", "lat"],
    get_radius=400,
    get_fill_color=[0, 128, 255],
    pickable=True
)

view_state = pdk.ViewState(
    latitude=filtered["lat"].mean() if len(filtered) else -2,
    longitude=filtered["lon"].mean() if len(filtered) else 118,
    zoom=6 if len(filtered) else 4
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{Desa}, {Kecamatan}, {Kab/Kota}, {Provinsi}"}
    )
)

# =======================
# 5. Pilih Lokasi & Ambil Prakiraan
# =======================
with col2:
    if len(filtered) > 0:
        selected = st.selectbox(
            "📍 Pilih lokasi untuk ambil prakiraan:",
            options=filtered.index,
            format_func=lambda i: (
                f"{filtered.loc[i, 'Desa']} - {filtered.loc[i, 'Kecamatan']} "
                f"({filtered.loc[i, 'Kab/Kota']})"
            )
        )

        if st.button("🌤️ Ambil Prakiraan Cuaca"):
            row = filtered.loc[selected]
            try:
                data = get_forecast(row.adm1, row.adm2, row.adm3, row.adm4)
                st.success(f"✅ Data cuaca untuk {row.Desa}, {row.Kecamatan}")
                # tampilkan ringkasan prakiraan
                if "data" in data:
                    for item in data["data"]:
                        nama = item.get("name")
                        tgl = item.get("tanggal")
                        cuaca = item.get("cuaca")
                        suhu = item.get("t")
                        st.write(f"📅 {tgl} | {nama} → {cuaca} ({suhu}°C)")
                else:
                    st.warning("Data prakiraan tidak tersedia.")
            except Exception as e:
                st.error(f"Gagal mengambil prakiraan cuaca: {e}")
    else:
        st.info("🔹 Masukkan nama daerah di kiri untuk memulai.")
