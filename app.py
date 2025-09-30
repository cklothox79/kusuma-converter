import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="🌦️")
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Daerah")

# ---------------------------
# Fungsi utilitas
# ---------------------------
def get_json(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        j = r.json()
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        elif isinstance(j, list):
            return j
        else:
            return []
    except Exception as e:
        st.error(f"⚠️ Kesalahan koneksi: {e}")
        return []

def safe_name(obj):
    """Ambil nama wilayah dari key yang ada."""
    for k in ["name","provinsi","kotkab","kecamatan","desa"]:
        if k in obj and obj[k]:
            return obj[k]
    return "-"

@st.cache_data(ttl=86400)
def get_all_locations():
    base = "https://cuaca.bmkg.go.id/api/df/v1/adm/list"
    provs = get_json(base)
    rows = []
    for p in provs:
        prov_name = safe_name(p)
        adm1 = p.get("adm1","")
        kab_list = get_json(f"{base}?adm1={adm1}")
        for k in kab_list:
            kab_name = safe_name(k)
            adm2 = k.get("adm2","")
            kec_list = get_json(f"{base}?adm1={adm1}&adm2={adm2}")
            for c in kec_list:
                kec_name = safe_name(c)
                adm3 = c.get("adm3","")
                desa_list = get_json(f"{base}?adm1={adm1}&adm2={adm2}&adm3={adm3}")
                for d in desa_list:
                    desa_name = safe_name(d)
                    rows.append({
                        "Provinsi": prov_name,
                        "Kab/Kota": kab_name,
                        "Kecamatan": kec_name,
                        "Desa": desa_name,
                        "adm1": adm1,
                        "adm2": adm2,
                        "adm3": adm3,
                        "adm4": d.get("adm4",""),
                    })
    return pd.DataFrame(rows)

def get_forecast(adm1, adm2, adm3, adm4):
    url = (
        f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
        f"?adm1={adm1}&adm2={adm2}&adm3={adm3}&adm4={adm4}"
    )
    data = get_json(url)
    if not data:
        return pd.DataFrame()
    if isinstance(data, list) and len(data)>0 and isinstance(data[0], dict) and "data" in data[0]:
        cuaca = data[0]["data"]
    else:
        cuaca = data
    if not cuaca:
        return pd.DataFrame()
    df = pd.DataFrame(cuaca)
    rename_map = {
        "jamCuaca":"Jam",
        "cuaca":"Kondisi",
        "kodeCuaca":"Kode",
        "tempC":"Suhu (°C)",
        "rh":"Kelembapan (%)"
    }
    return df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})

# ---------------------------
# UI
# ---------------------------
nama = st.text_input("Masukkan nama daerah (Provinsi/Kabupaten/Kecamatan/Desa):","Simogirang")

if st.button("Cari"):
    if not nama.strip():
        st.warning("Silakan masukkan nama daerah.")
    else:
        st.info("🔍 Mengambil dan memfilter daftar wilayah...")
        df = get_all_locations()
        if df.empty:
            st.error("❌ Tidak bisa mengambil daftar wilayah.")
        else:
            mask = (
                df["Provinsi"].str.contains(nama, case=False, na=False) |
                df["Kab/Kota"].str.contains(nama, case=False, na=False) |
                df["Kecamatan"].str.contains(nama, case=False, na=False) |
                df["Desa"].str.contains(nama, case=False, na=False)
            )
            hasil = df[mask]
            if hasil.empty:
                st.error("❌ Wilayah tidak ditemukan.")
            else:
                st.success(f"✅ Ditemukan {len(hasil)} lokasi:")
                st.dataframe(hasil, use_container_width=True)

                idx = st.selectbox(
                    "Pilih lokasi:",
                    hasil.index,
                    format_func=lambda i: (
                        f"{hasil.loc[i,'Desa']} - {hasil.loc[i,'Kecamatan']} - "
                        f"{hasil.loc[i,'Kab/Kota']} - {hasil.loc[i,'Provinsi']}"
                    )
                )

                row = hasil.loc[idx]
                st.info(f"🌐 Mengambil prakiraan cuaca untuk: {row['Desa']}, {row['Kecamatan']}")

                cuaca_df = get_forecast(row.adm1,row.adm2,row.adm3,row.adm4)
                if cuaca_df.empty:
                    st.error("❌ Data prakiraan cuaca tidak tersedia.")
                else:
                    st.dataframe(cuaca_df, use_container_width=True)
