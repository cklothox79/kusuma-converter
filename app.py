import streamlit as st
import requests

BASE = "https://cuaca.bmkg.go.id/api/df/v1"

@st.cache_data(show_spinner=False)
def get_list(adm1=None, adm2=None, adm3=None):
    """Ambil daftar wilayah sesuai level (dengan pengecekan error)."""
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    try:
        r = requests.get(f"{BASE}/adm/list", params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        else:
            # Jika format tak sesuai
            st.warning(f"Format JSON tidak sesuai. Response: {j}")
            return []
    except Exception as e:
        st.error(f"Gagal memanggil API BMKG: {e}")
        return []

st.title("Prakiraan Cuaca BMKG by Nama Wilayah")

provinsi  = st.text_input("Provinsi", "Jawa Timur")
kabupaten = st.text_input("Kab/Kota", "Sidoarjo")
kecamatan = st.text_input("Kecamatan", "Buduran")
kelurahan = st.text_input("Kelurahan/Desa", "Sidokerto")

if st.button("Cari Data"):
    try:
        prov = next(
            (p for p in get_list() if provinsi.lower() in p.get("name","").lower()), 
            None
        )
        if not prov:
            st.error("Provinsi tidak ditemukan.")
            st.stop()

        kab = next(
            (k for k in get_list(prov["adm1"]) if kabupaten.lower() in k.get("name","").lower()),
            None
        )
        if not kab:
            st.error("Kab/Kota tidak ditemukan.")
            st.stop()

        kec = next(
            (k for k in get_list(prov["adm1"], kab["adm2"]) if kecamatan.lower() in k.get("name","").lower()),
            None
        )
        if not kec:
            st.error("Kecamatan tidak ditemukan.")
            st.stop()

        kel = next(
            (k for k in get_list(prov["adm1"], kab["adm2"], kec["adm3"]) if kelurahan.lower() in k.get("name","").lower()),
            None
        )
        if not kel:
            st.error("Kelurahan/Desa tidak ditemukan.")
            st.stop()

        # --- Ambil prakiraan cuaca ---
        params = dict(adm1=prov["adm1"], adm2=kab["adm2"], adm3=kec["adm3"], adm4=kel["adm4"])
        try:
            r = requests.get(f"{BASE}/forecast/adm", params=params, timeout=10)
            r.raise_for_status()
            j = r.json()
            if "data" in j:
                st.success(f"Kode Wilayah: {prov['adm1']}-{kab['adm2']}-{kec['adm3']}-{kel['adm4']}")
                st.json(j["data"])
            else:
                st.warning(f"Tidak ada data prakiraan. Response: {j}")
        except Exception as e:
            st.error(f"Gagal memanggil prakiraan: {e}")

    except Exception as e:
        st.exception(e)
