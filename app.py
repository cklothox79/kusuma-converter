# app.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px

st.set_page_config(page_title="🌦️ Prakiraan Harian & Dinamika Atmosfer — Jawa Timur", layout="wide")
st.title("🌦️ Prakiraan Harian & Dinamika Atmosfer — Jawa Timur")
st.write("Fusion: BMKG (jika tersedia) + Open-Meteo. Mudah dipahami publik — input cukup nama desa/kecamatan/kabupaten.")

# -------------------------
# 1) Load local kode_wilayah.csv (root repo)
# -------------------------
CSV_PATH = "kode_wilayah.csv"  # file ada di root repo; ubah path jika dipindah ke /data/

@st.cache_data(ttl=3600)
def load_wilayah(csv_path=CSV_PATH):
    try:
        df = pd.read_csv(csv_path, dtype=str, encoding='utf-8')
        # normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        if 'kode' not in df.columns or 'nama' not in df.columns:
            st.error("File CSV perlu kolom minimal: 'kode' dan 'nama'.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Gagal membaca {csv_path}: {e}")
        return pd.DataFrame()

wilayah_df = load_wilayah()

if wilayah_df.empty:
    st.stop()

# -------------------------
# 2) Input user & cari kecocokan (contains search)
# -------------------------
st.sidebar.header("Pencarian Lokasi")
nama_input = st.sidebar.text_input("Ketik nama desa/kecamatan/kabupaten (contoh: Simogirang)", "")

# optional: show examples top 10
if st.sidebar.button("Tampilkan contoh nama (10 teratas)"):
    st.sidebar.write(wilayah_df["nama"].dropna().head(50).tolist()[:50])

selected_row = None
if nama_input:
    matches = wilayah_df[wilayah_df["nama"].str.contains(nama_input, case=False, na=False)]
    if len(matches) == 0:
        st.warning("Nama daerah tidak ditemukan di CSV lokal. Coba ejaan lain atau tambahkan kata kunci kabupaten/kota.")
    elif len(matches) == 1:
        selected_row = matches.iloc[0]
    else:
        # jika banyak hasil, beri pilihan
        choice = st.sidebar.selectbox("Pilih hasil yang tepat:", matches["nama"].tolist())
        selected_row = matches[matches["nama"] == choice].iloc[0]

# -------------------------
# Helpers: geocoding fallback (Open-Meteo) dan resolusi adm4
# -------------------------
@st.cache_data(ttl=3600)
def geocode_open_meteo(name):
    """Fallback: jika tidak ada koordinat di CSV, gunakan geocoding Open-Meteo."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(name)}&count=1&language=id&countryCode=ID"
        r = requests.get(url, timeout=10).json()
        if "results" in r and len(r["results"])>0:
            res = r["results"][0]
            return float(res["latitude"]), float(res["longitude"]), res.get("name",""), res.get("admin1","")
    except Exception:
        return None
    return None

def find_adm4_from_csv(base_code):
    """
    Jika kode pada baris yang dipilih bukan adm4, cari descendant di CSV yang merupakan adm4:
    adm4 terlihat sebagai kode dengan 4 segmen (contoh 35.15.02.2018)
    """
    if pd.isna(base_code):
        return None
    parts = str(base_code).split('.')
    if len(parts) >= 4:
        return base_code  # sudah adm4
    # cari kode yang dimulai dengan base_code + '.' dan yang memiliki 4 segmen
    candidates = wilayah_df[wilayah_df["kode"].str.startswith(base_code + ".")]
    for c in candidates["kode"].unique():
        if len(c.split('.')) >= 4:
            return c
    return None

# -------------------------
# 3) Data fetching: BMKG attempt (adm4 or adm1), otherwise Open-Meteo
# -------------------------
def fetch_bmkg_by_adm(adm_key, adm_level='adm4'):
    """
    Try to fetch BMKG forecast by adm4 (preferred) or adm1 (province) if available.
    adm_key: code like '35.15.02.2018' or '35'
    """
    try:
        # Example endpoint discovered: /api/df/v1/forecast/adm?adm4=...
        url = f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm?{adm_level}={adm_key}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=300)
def fetch_open_meteo(lat, lon):
    # hourly parameters for 1 day (today)
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relativehumidity_2m,cloudcover,precipitation,precipitation_probability,windspeed_10m,winddirection_10m",
            "forecast_days": 1,
            "timezone": "Asia/Jakarta"
        }
        url = "https://api.open-meteo.com/v1/forecast"
        r = requests.get(url, params=params, timeout=12)
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_metar_nearby(station="WARR"):
    """
    Try to fetch METAR text from NOAA TGFTP (OGIMET sometimes) for Juanda WARR.
    This is optional and best-effort only.
    """
    try:
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            txt = r.text.strip().splitlines()
            return txt[-1] if txt else None
    except Exception:
        pass
    return None

# -------------------------
# 4) When user selected a location: resolve coords & codes, fetch data, analyze
# -------------------------
if selected_row is not None:
    st.markdown("## Hasil Pencarian")
    st.write(f"**Nama (CSV):** {selected_row['nama']}  \n**Kode wilayah:** {selected_row['kode']}")
    # try read lat/lon columns if present in CSV
    lat = None
    lon = None
    for col in ['lat','latitude','y','latit','lintang']:
        if col in wilayah_df.columns and not pd.isna(selected_row.get(col, np.nan)):
            try:
                lat = float(selected_row[col])
            except Exception:
                lat = None
    for col in ['lon','longitude','x','longit','bujur']:
        if col in wilayah_df.columns and not pd.isna(selected_row.get(col, np.nan)):
            try:
                lon = float(selected_row[col])
            except Exception:
                lon = None

    # if no coords in CSV, geocode fallback
    if lat is None or lon is None:
        geo = geocode_open_meteo(selected_row['nama'] + " Jawa Timur")
        if geo:
            lat, lon, geo_name, geo_admin = geo
            st.info(f"Koordinat diambil dari geocoding: {lat:.5f}, {lon:.5f} ({geo_name}, {geo_admin})")
        else:
            st.error("Gagal mendapatkan koordinat untuk lokasi ini. Coba nama lain atau tambahkan kabupaten/kota.")
            st.stop()
    else:
        st.info(f"Koordinat diambil dari CSV: {lat:.5f}, {lon:.5f}")

    # attempt to resolve adm4 code (BMKG) from CSV code
    code = str(selected_row['kode']).strip()
    adm4_code = find_adm4_from_csv(code)
    bmkg_data = None
    if adm4_code and adm4_code.startswith("35"):  # 35 = Jawa Timur
        bmkg_data = fetch_bmkg_by_adm(adm4_code, adm_level='adm4')
    # if BMKG not found at adm4 try adm1 (province)
    if bmkg_data is None:
        # try adm1 (first segment)
        adm1 = code.split('.')[0] if '.' in code else code
        if adm1 == '35':
            bmkg_data = fetch_bmkg_by_adm(adm1, adm_level='adm1')

    # fetch Open-Meteo always as fallback / fusion
    openm = fetch_open_meteo(lat, lon)

    # fetch METAR (Juanda) best-effort
    metar_text = fetch_metar_nearby("WARR")

    # -------------------------
    # 5) Prepare user-friendly narrative (pagi/siang/malam)
    # -------------------------
    def summarize_day_from_openm(openm_json):
        if not openm_json or "hourly" not in openm_json:
            return None
        h = openm_json["hourly"]
        times = pd.to_datetime(h["time"])
        dfh = pd.DataFrame({
            "time": times,
            "temp": h.get("temperature_2m", []),
            "rh": h.get("relativehumidity_2m", []),
            "cloud": h.get("cloudcover", []),
            "precip": h.get("precipitation", []),
            "pop": h.get("precipitation_probability", []),
            "wind": h.get("windspeed_10m", []),
            "wdir": h.get("winddirection_10m", []),
        })
        dfh["hour"] = dfh["time"].dt.hour

        def agg(h0,h1):
            seg = dfh[(dfh["hour"]>=h0)&(dfh["hour"]<h1)]
            if seg.empty:
                return {"temp": None,"rh":None,"cloud":None,"precip":0,"pop":0,"wind":None}
            return {
                "temp": round(float(seg["temp"].mean()),1),
                "rh": round(float(seg["rh"].mean()),1),
                "cloud": round(float(seg["cloud"].mean()),1),
                "precip": round(float(seg["precip"].sum()),2),
                "pop": round(float(seg["pop"].mean()),1),
                "wind": round(float(seg["wind"].mean()),1)
            }
        pagi = agg(6,12)
        siang = agg(12,18)
        malam = agg(18,24)
        return {"pagi":pagi,"siang":siang,"malam":malam,"dfh":dfh}

    summary = summarize_day_from_openm(openm)

    # build narrative using BMKG if available (prefer BMKG fields), else open-meteo summary
    st.markdown("### Hasil Prakiraan (Ringkasan Hari Ini)")
    if bmkg_data:
        # BMKG endpoint format may vary; try to present meaningful pieces if present
        st.info("Sumber utama: BMKG (ketika tersedia). Data BMKG digunakan bersama Open-Meteo untuk fusi.")
        # try to extract some human readable text if BMKG provides it
        try:
            # BMKG JSON structures vary; try common keys
            if isinstance(bmkg_data, dict) and "data" in bmkg_data:
                st.write("BMKG (potongan data):")
                st.write(bmkg_data.get("data") if len(str(bmkg_data.get("data")))<1000 else "BMKG data tersedia (besar).")
        except Exception:
            pass
    else:
        st.info("Sumber utama: Open-Meteo (BMKG tidak tersedia untuk kode ini atau panggilan gagal).")

    # print METAR latest if any
    if metar_text:
        st.markdown("**Observasi METAR (WARR - Juanda) — terbaru:**")
        st.code(metar_text, language="text")

    if summary:
        # readable narrative
        def readable(seg, name):
            if seg["temp"] is None:
                return f"- **{name}:** Data tidak tersedia."
            desc = ""
            if seg["precip"] > 5 or seg["pop"] > 60:
                desc = "berpotensi hujan sedang hingga lebat"
            elif seg["precip"] > 1 or seg["pop"] > 30:
                desc = "berpotensi hujan ringan"
            elif seg["cloud"] > 70:
                desc = "berawan tebal"
            elif seg["cloud"] > 40:
                desc = "cerah berawan"
            else:
                desc = "cerah"

            return f"- **{name}:** {desc}. Suhu ~{seg['temp']}°C, kelembapan ~{seg['rh']}%, peluang hujan ~{seg['pop']}%, kecepatan angin ~{seg['wind']} km/jam."

        st.markdown(f"**Lokasi:** {selected_row['nama']}  \n**Koordinat:** {lat:.5f}, {lon:.5f}")
        st.markdown("**Narasi ringkas (pagi / siang / malam)**")
        st.write(readable(summary["pagi"], "Pagi (06–12 WIB)"))
        st.write(readable(summary["siang"], "Siang (12–18 WIB)"))
        st.write(readable(summary["malam"], "Malam (18–24 WIB)"))

        # -------------------------
        # Dynamical insight (heuristic fusion)
        # -------------------------
        st.markdown("### 🌬️ Analisis Dinamika Atmosfer (heuristik, publik)")
        # simple heuristics:
        dyn_msgs = []
        try:
            dfh = summary["dfh"]
            # variability of wind vector magnitude over the day (temporal convergence proxy)
            dfh["u"] = dfh["wind"] * np.cos(np.deg2rad(dfh["wdir"]))
            dfh["v"] = dfh["wind"] * np.sin(np.deg2rad(dfh["wdir"]))
            # compute mean absolute successive differences as proxy for convergence/change
            u_diff = np.mean(np.abs(np.diff(dfh["u"].fillna(0))))
            v_diff = np.mean(np.abs(np.diff(dfh["v"].fillna(0))))
            wind_var = float(np.round((u_diff+v_diff)/2,3))
            mean_rh = float(dfh["rh"].mean())
            mean_cloud = float(dfh["cloud"].mean())
            total_precip = float(dfh["precip"].sum())

            if wind_var > 1.5 and mean_rh > 75:
                dyn_msgs.append("Terdapat indikasi pertemuan atau perubahan arah/kecepatan angin signifikan (proxy konvergensi) bersamaan dengan kelembapan tinggi → potensi hujan konvektif lokal meningkat.")
            elif total_precip > 5:
                dyn_msgs.append("Terlihat akumulasi curah hujan yang cukup hari ini — kemungkinan sistem hujan lokal atau garis konvergensi.")
            elif mean_cloud > 60 and mean_rh > 70:
                dyn_msgs.append("Awan dan kelembapan cukup tinggi — waspadai pembentukan awan konvektif terutama sore hari.")
            else:
                dyn_msgs.append("Tidak terdeteksi indikasi konvergensi kuat; kondisi relatif stabil hari ini.")

            # add METAR hint
            if metar_text and any(x in metar_text for x in ["TS","SH","RA","DZ","FG"]):
                dyn_msgs.append("Observasi METAR menunjukkan adanya fenomena (TS/SH/RA/FG) di stasiun Juanda; ini bisa memperkuat/menandai kondisi lokal.")
        except Exception:
            dyn_msgs.append("Analisis dinamika atmosfer tidak tersedia atau gagal dihitung.")

        for m in dyn_msgs:
            st.info(m)

        # -------------------------
        # 6) Visual: chart per jam (suhu & precip)
        # -------------------------
        st.markdown("### 📊 Grafik Per Jam (Suhu & Curah Hujan)")
        dfv = summary["dfh"]
        fig = px.line(dfv, x="time", y=["temp","precip"], labels={"value":"Nilai","time":"Waktu"}, title="Suhu (°C) & Curah Hujan (mm) per Jam")
        st.plotly_chart(fig, use_container_width=True)

        # simple map (marker)
        st.markdown("### 🗺️ Lokasi pada Peta")
        st.map(pd.DataFrame({"lat":[lat], "lon":[lon]}), zoom=10)

        st.caption("Catatan: Analisis dinamika atmosfer bersifat heuristik (proxy) berbasis data permukaan per jam; untuk analisis dinamis yang presisi diperlukan data vektor angin pada beberapa grid (level tekanan) dan analisis lapangan yang lebih mendalam.")
    else:
        st.error("Data prakiraan tidak tersedia (BMKG & Open-Meteo gagal).")
