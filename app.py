import streamlit as st
import requests

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="⛅")

BASE = "https://cuaca.bmkg.go.id/api/df/v1"

# ---------- Helper ----------
@st.cache_data(show_spinner=False)
def get_list(adm1=None, adm2=None, adm3=None):
    """Ambil daftar wilayah sesuai level."""
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    try:
        r = requests.get(f"{BASE}/adm/list", params=params, timeout=15)
        r.raise_for_status()
        j = r.json()
        # API terbaru langsung berupa list
        return j if isinstance(j, list) else j.get("data", [])
    except Exception as e:
        st.error(f"Gagal ambil list: {e}")
        return []


@st.cache_data(show_spinner=False)
def get_forecast(adm1, adm2, adm3, adm4):
    """Ambil prakiraan cuaca berdasarkan kode wilayah."""
    try:
        params = dict(adm1=adm1, adm2=adm2, adm3=adm3, adm4=adm4)
        r = requests.get(f"{BASE}/forecast/adm", params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Gagal ambil data prakiraan: {e}")
        return {}

def find_by_name(data, key, name):
    name = (name or "").lower()
    return next((d for d in data if name in (d.get(key) or "").lower()), None)

# ---------- UI ----------
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Wilayah")

prov_name = st.text_input("Provinsi", "Jawa Timur")
kab_name  = st.text_input("Kab/Kota", "Sidoarjo")
kec_name  = st.text_input("Kecamatan", "Prambon")
des_name  = st.text_input("Kelurahan/Desa", "Simogirang")

if st.button("Cari Data"):
    # Cari provinsi
    prov_list = get_list()
    prov = find_by_name(prov_list, "provinsi", prov_name)
    if not prov:
        st.error("Provinsi tidak ditemukan.")
        st.stop()
    st.success(f"Provinsi: {prov['provinsi']} ({prov['adm1']})")

    # Cari kabupaten
    kab_list = get_list(prov["adm1"])
    kab = find_by_name(kab_list, "kotkab", kab_name)
    if not kab:
        st.error("Kab/Kota tidak ditemukan.")
        st.stop()
    st.success(f"Kab/Kota: {kab['kotkab']} ({kab['adm2']})")

    # Cari kecamatan
    kec_list = get_list(prov["adm1"], kab["adm2"])
    kec = find_by_name(kec_list, "kecamatan", kec_name)
    if not kec:
        st.error("Kecamatan tidak ditemukan.")
        st.stop()
    st.success(f"Kecamatan: {kec['kecamatan']} ({kec['adm3']})")

    # Cari desa
    des_list = get_list(prov["adm1"], kab["adm2"], kec["adm3"])
    des = find_by_name(des_list, "desa", des_name)
    if not des:
        st.error("Desa tidak ditemukan.")
        st.stop()
    st.success(f"Desa: {des['desa']} ({des['adm4']})")

    # Ambil prakiraan cuaca
    forecast = get_forecast(prov["adm1"], kab["adm2"], kec["adm3"], des["adm4"])
    if "data" in forecast:
        st.subheader("📊 Data Prakiraan Cuaca")
        st.json(forecast)
    else:
        st.warning("Data prakiraan belum tersedia.")
