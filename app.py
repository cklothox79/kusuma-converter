import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="🌦️")
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Daerah")

@st.cache_data(ttl=86400)
def get_all_locations():
    base = "https://cuaca.bmkg.go.id/api/df/v1/adm/list"
    provs = requests.get(base).json()["data"]
    rows = []
    for p in provs:
        kab = requests.get(f"{base}?adm1={p['adm1']}").json()["data"]
        for k in kab:
            kec = requests.get(f"{base}?adm1={p['adm1']}&adm2={k['adm2']}").json()["data"]
            for c in kec:
                desa = requests.get(
                    f"{base}?adm1={p['adm1']}&adm2={k['adm2']}&adm3={c['adm3']}"
                ).json()["data"]
                for d in desa:
                    rows.append({
                        "prov": p["name"],
                        "kab": k["name"],
                        "kec": c["name"],
                        "desa": d["name"],
                        "adm1": p["adm1"],
                        "adm2": k["adm2"],
                        "adm3": c["adm3"],
                        "adm4": d["adm4"]
                    })
    return pd.DataFrame(rows)

nama = st.text_input("Masukkan nama daerah:", "Sidomulyo")

if st.button("Cari"):
    st.write("🔍 Mengambil dan memfilter daftar wilayah...")
    try:
        df = get_all_locations()
        mask = (
            df["prov"].str.contains(nama, case=False) |
            df["kab"].str.contains(nama, case=False) |
            df["kec"].str.contains(nama, case=False) |
            df["desa"].str.contains(nama, case=False)
        )
        hasil = df[mask]
        if hasil.empty:
            st.error("Wilayah tidak ditemukan.")
        else:
            st.dataframe(hasil)
            idx = st.selectbox("Pilih lokasi:", hasil.index,
                               format_func=lambda i: f"{hasil.loc[i,'desa']} - {hasil.loc[i,'kec']} ({hasil.loc[i,'kab']})")
            row = hasil.loc[idx]
            url = (
                f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
                f"?adm1={row.adm1}&adm2={row.adm2}&adm3={row.adm3}&adm4={row.adm4}"
            )
            r = requests.get(url).json()
            st.json(r)  # atau diolah jadi tabel
    except Exception as e:
        st.error(f"⚠️ Kesalahan koneksi: {e}")
