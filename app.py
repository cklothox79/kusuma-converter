import streamlit as st
import requests

st.set_page_config(page_title="Prakiraan Cuaca BMKG by Nama", page_icon="⛅")

BASE = "https://cuaca.bmkg.go.id/api/df/v1"


# =========================
# Fungsi Helper
# =========================
@st.cache_data(show_spinner=False)
def get_list(adm1=None, adm2=None, adm3=None):
    """Ambil daftar wilayah sesuai level (prov, kab, kec, desa)."""
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    try:
        r = requests.get(f"{BASE}/adm/list", params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        # API baru: langsung list
        if isinstance(j, list):
            return j
        # fallback API lama
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        return []
    except Exception as e:
        st.error(f"Gagal mengambil daftar wilayah: {e}")
        return []


@st.cache_data(show_spinner=False)
def get_forecast(adm1, adm2, adm3, adm4):
    """Ambil prakiraan cuaca desa/kelurahan."""
    try:
        params = dict(adm1=adm1, adm2=adm2, adm3=adm3, adm4=adm4)
        r = requests.get(f"{BASE}/forecast/adm", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Gagal mengambil data prakiraan: {e}")
        return {}


def find_by_name(data, name_key, keyword):
    """Cari dict pada list berdasarkan nama (case-insensitive)."""
    keyword = (keyword or "").strip().lower()
    if not keyword:
        return None
    return next(
        (item for item in data if keyword in (item.get(name_key) or "").lower()),
        None
    )


# =========================
# UI Streamlit
# =========================
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Wilayah")

# --- Provinsi
prov_input = st.text_input("Provinsi", placeholder="Contoh: Jawa Timur")
prov_data = get_list()
prov = find_by_name(prov_data, "provinsi", prov_input)

if prov:
    st.success(f"Provinsi ditemukan: {prov['provinsi']} (adm1={prov['adm1']})")

    # --- Kab/Kota
    kab_input = st.text_input("Kab/Kota", placeholder="Contoh: Sidoarjo")
    kab_data = get_list(adm1=prov["adm1"])
    kab = find_by_name(kab_data, "kotkab", kab_input)

    if kab:
        st.success(f"Kab/Kota ditemukan: {kab['kotkab']} (adm2={kab['adm2']})")

        # --- Kecamatan
        kec_input = st.text_input("Kecamatan", placeholder="Contoh: Buduran")
        kec_data = get_list(adm1=prov["adm1"], adm2=kab["adm2"])
        kec = find_by_name(kec_data, "kecamatan", kec_input)

        if kec:
            st.success(f"Kecamatan ditemukan: {kec['kecamatan']} (adm3={kec['adm3']})")

            # --- Desa
            desa_input = st.text_input("Kelurahan/Desa", placeholder="Contoh: Sidokerto")
            desa_data = get_list(adm1=prov["adm1"], adm2=kab["adm2"], adm3=kec["adm3"])
            desa = find_by_name(desa_data, "desa", desa_input)

            if desa:
                st.success(f"Desa ditemukan: {desa['desa']} (adm4={desa['adm4']})")

                if st.button("Ambil Prakiraan Cuaca"):
                    data = get_forecast(
                        prov["adm1"], kab["adm2"], kec["adm3"], desa["adm4"]
                    )
                    if data:
                        st.subheader("📊 Prakiraan Cuaca")
                        st.json(data)
            else:
                st.info("Masukkan nama desa/kelurahan yang sesuai.")
        else:
            st.info("Masukkan nama kecamatan yang sesuai.")
    else:
        st.info("Masukkan nama kab/kota yang sesuai.")
else:
    if prov_input:
        st.error("Provinsi tidak ditemukan.")
