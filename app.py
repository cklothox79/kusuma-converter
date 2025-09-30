import requests

BASE = "https://cuaca.bmkg.go.id/api/df/v1"

def get_list(adm1=None, adm2=None, adm3=None):
    """Ambil daftar wilayah sesuai level"""
    params = {}
    if adm1: params["adm1"] = adm1
    if adm2: params["adm2"] = adm2
    if adm3: params["adm3"] = adm3
    r = requests.get(f"{BASE}/adm/list", params=params)
    r.raise_for_status()
    return r.json()["data"]

def search_region(province_name, kabupaten_name, kecamatan_name, kelurahan_name):
    # 1️⃣ Cari provinsi
    prov_list = get_list()
    prov = next((p for p in prov_list if province_name.lower() in p["name"].lower()), None)
    if not prov:
        raise ValueError("Provinsi tidak ditemukan")
    adm1 = prov["adm1"]

    # 2️⃣ Cari kab/kota
    kab_list = get_list(adm1=adm1)
    kab = next((k for k in kab_list if kabupaten_name.lower() in k["name"].lower()), None)
    if not kab:
        raise ValueError("Kab/Kota tidak ditemukan")
    adm2 = kab["adm2"]

    # 3️⃣ Cari kecamatan
    kec_list = get_list(adm1=adm1, adm2=adm2)
    kec = next((k for k in kec_list if kecamatan_name.lower() in k["name"].lower()), None)
    if not kec:
        raise ValueError("Kecamatan tidak ditemukan")
    adm3 = kec["adm3"]

    # 4️⃣ Cari kelurahan/desa
    kel_list = get_list(adm1=adm1, adm2=adm2, adm3=adm3)
    kel = next((k for k in kel_list if kelurahan_name.lower() in k["name"].lower()), None)
    if not kel:
        raise ValueError("Kelurahan tidak ditemukan")
    adm4 = kel["adm4"]

    return adm1, adm2, adm3, adm4

def get_forecast(adm1, adm2, adm3, adm4):
    url = f"{BASE}/forecast/adm"
    params = dict(adm1=adm1, adm2=adm2, adm3=adm3, adm4=adm4)
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

# ⚡ Contoh pemakaian
if __name__ == "__main__":
    # Ganti sesuai kebutuhan
    prov, kab, kec, kel = search_region(
        province_name="Jawa Timur",
        kabupaten_name="Sidoarjo",
        kecamatan_name="Buduran",
        kelurahan_name="Sidokerto"
    )
    data = get_forecast(prov, kab, kec, kel)
    print(f"Kode wilayah: {prov}-{kab}-{kec}-{kel}")
    # tampilkan prakiraan pertama saja
    print(data["data"][0])
