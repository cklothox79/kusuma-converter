import streamlit as st
import requests

BASE = "https://cuaca.bmkg.go.id/api/df/v1"

@st.cache_data
def get_list(adm1=None, adm2=None, adm3=None):
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    r = requests.get(f"{BASE}/adm/list", params=params)
    return r.json()["data"]

st.title("Prakiraan Cuaca BMKG by Nama Wilayah")

provinsi = st.text_input("Provinsi", "Jawa Timur")
kabupaten = st.text_input("Kab/Kota", "Sidoarjo")
kecamatan = st.text_input("Kecamatan", "Buduran")
kelurahan = st.text_input("Kelurahan/Desa", "Sidokerto")

if st.button("Cari Data"):
    try:
        # --- pencarian kode ---
        prov = next(p for p in get_list() if provinsi.lower() in p["name"].lower())
        kab = next(k for k in get_list(prov["adm1"]) if kabupaten.lower() in k["name"].lower())
        kec = next(k for k in get_list(prov["adm1"], kab["adm2"]) if kecamatan.lower() in k["name"].lower())
        kel = next(k for k in get_list(prov["adm1"], kab["adm2"], kec["adm3"]) if kelurahan.lower() in k["name"].lower())

        # --- prakiraan ---
        url = f"{BASE}/forecast/adm"
        params = dict(adm1=prov["adm1"], adm2=kab["adm2"], adm3=kec["adm3"], adm4=kel["adm4"])
        forecast = requests.get(url, params=params).json()

        st.success(f"Kode Wilayah: {prov['adm1']}-{kab['adm2']}-{kec['adm3']}-{kel['adm4']}")
        st.json(forecast["data"])
    except StopIteration:
        st.error("Nama wilayah tidak ditemukan")
