import streamlit as st
import requests

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG – Jawa", layout="wide")

# =======================
# 1. Daftar Provinsi Jawa
# =======================
PROV_JAWA = {
    "Banten": "36",
    "DKI Jakarta": "31",
    "Jawa Barat": "32",
    "Jawa Tengah": "33",
    "DI Yogyakarta": "34",
    "Jawa Timur": "35",
}

@st.cache_data
def get_list(adm1=None, adm2=None, adm3=None):
    """
    Ambil daftar wilayah sesuai level.
    adm1 = kode provinsi
    adm2 = kode kab/kota
    adm3 = kode kecamatan
    """
    base = "https://cuaca.bmkg.go.id/api/df/v1/adm/list"
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    r = requests.get(base, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data
def get_forecast(adm1, adm2, adm3, adm4):
    url = (
        f"https://cuaca.bmkg.go.id/api/df/v1/forecast/adm?"
        f"adm1={adm1}&adm2={adm2}&adm3={adm3}&adm4={adm4}"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

st.title("🌦️ Prakiraan Cuaca BMKG – Pulau Jawa")

# =======================
# 2. Pilihan Provinsi
# =======================
prov_name = st.selectbox("🟢 Pilih Provinsi", list(PROV_JAWA.keys()))
adm1 = PROV_JAWA[prov_name]

# =======================
# 3. Pilihan Kab/Kota
# =======================
kab_list = get_list(adm1=adm1)
kab_name = st.selectbox("🏙️ Pilih Kabupaten/Kota", [k["name"] for k in kab_list])
adm2 = next(k["adm2"] for k in kab_list if k["name"] == kab_name)

# =======================
# 4. Pilihan Kecamatan
# =======================
kec_list = get_list(adm1=adm1, adm2=adm2)
kec_name = st.selectbox("🏡 Pilih Kecamatan", [k["name"] for k in kec_list])
adm3 = next(k["adm3"] for k in kec_list if k["name"] == kec_name)

# =======================
# 5. Pilihan Desa/Kelurahan
# =======================
desa_list = get_list(adm1=adm1, adm2=adm2, adm3=adm3)
desa_name = st.selectbox("🌿 Pilih Desa/Kelurahan", [k["name"] for k in desa_list])
adm4 = next(k["adm4"] for k in desa_list if k["name"] == desa_name)

# =======================
# 6. Ambil Prakiraan
# =======================
if st.button("🌤️ Ambil Prakiraan Cuaca"):
    try:
        data = get_forecast(adm1, adm2, adm3, adm4)
        st.success(f"✅ Prakiraan Cuaca untuk {desa_name}, {kec_name}")
        if "data" in data:
            for d in data["data"]:
                tgl = d.get("tanggal")
                cuaca = d.get("cuaca")
                suhu = d.get("t")
                st.write(f"📅 {tgl} → {cuaca} ({suhu}°C)")
        else:
            st.warning("Data prakiraan tidak tersedia.")
    except Exception as e:
        st.error(f"Gagal mengambil prakiraan cuaca: {e}")
