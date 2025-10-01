import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Cuaca BMKG", page_icon="🌦️", layout="wide")
st.title("🌦️ Prakiraan Cuaca Desa Simogirang")

# --- ADM CODE ---
ADM4 = "35.15.02.2018"   # Desa Simogirang
ADM3 = "35.15.02"        # Kecamatan Prambon
ADM2 = "35.15"           # Kab. Sidoarjo

def ambil_data(adm_code):
    url = f"https://api-apps.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm_code}"
    try:
        r = requests.get(url, timeout=10)
        if r.ok and r.text.strip() != "":
            return r.json()
        else:
            return None
    except Exception:
        return None

# --- Coba urut ADM4 → ADM3 → ADM2 ---
data = ambil_data(ADM4)
if data is None:
    st.warning("⚠️ Data ADM4 kosong, mencoba ADM3...")
    data = ambil_data(ADM3)
if data is None:
    st.warning("⚠️ Data ADM3 kosong, mencoba ADM2...")
    data = ambil_data(ADM2)

if data is None:
    st.error("❌ Gagal ambil data BMKG di semua level wilayah")
    st.stop()

st.success("✅ Data BMKG berhasil diambil")

# --- Parsing Data ---
try:
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

    # === WEATHER CARD ===
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

    # === GRAFIK TREN ===
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
    st.error(f"⚠️ Gagal parsing data BMKG: {e}")
    st.json(data)  # debug fallback
