import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="🌦️", layout="centered")
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Daerah")

@st.cache_data(show_spinner=False, ttl=3600)
def ambil_daftar_wilayah():
    url = "https://api-apps.bmkg.go.id/publik/prakiraan-cuaca/wilayah"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.DataFrame(r.json()["data"])

nama_daerah = st.text_input("Masukkan nama daerah (Provinsi/Kabupaten/Kecamatan/Desa):", "Simogirang")

if st.button("Cari Prakiraan Cuaca"):
    if not nama_daerah.strip():
        st.warning("Silakan masukkan nama daerah terlebih dahulu.")
    else:
        try:
            st.write("🔍 Mengambil dan memfilter daftar wilayah BMKG...")
            df_wilayah = ambil_daftar_wilayah()

            # Filter bebas di semua level
            mask = (
                df_wilayah["adm1"].str.contains(nama_daerah, case=False, na=False) |
                df_wilayah["adm2"].str.contains(nama_daerah, case=False, na=False) |
                df_wilayah["adm3"].str.contains(nama_daerah, case=False, na=False) |
                df_wilayah["adm4"].str.contains(nama_daerah, case=False, na=False)
            )
            hasil = df_wilayah[mask]

            if hasil.empty:
                st.error("❌ Wilayah tidak ditemukan. Coba nama lain (misal: 'Prambon', 'Sidoarjo').")
            else:
                hasil_display = hasil[["adm1", "adm2", "adm3", "adm4", "id"]]
                st.dataframe(hasil_display, use_container_width=True)

                pilihan = st.selectbox(
                    "Pilih Wilayah:",
                    hasil_display.index,
                    format_func=lambda i: f"{hasil_display.loc[i,'adm4']} - "
                                          f"{hasil_display.loc[i,'adm3']} - "
                                          f"{hasil_display.loc[i,'adm2']} - "
                                          f"{hasil_display.loc[i,'adm1']}"
                )

                wilayah_id = hasil_display.loc[pilihan, "id"]
                cuaca_url = f"https://api-apps.bmkg.go.id/publik/prakiraan-cuaca?adm4={wilayah_id}"
                st.write(f"🌐 Mengambil prakiraan cuaca untuk ID: `{wilayah_id}` ...")
                cuaca_resp = requests.get(cuaca_url, timeout=20)
                cuaca_resp.raise_for_status()
                cuaca_data = cuaca_resp.json()

                if "data" not in cuaca_data or not cuaca_data["data"]:
                    st.error("❌ Tidak ada data prakiraan cuaca.")
                else:
                    df_cuaca = pd.DataFrame(cuaca_data["data"][0]["cuaca"])
                    df_cuaca = df_cuaca.rename(columns={
                        "jamCuaca": "Jam",
                        "kodeCuaca": "Kode",
                        "cuaca": "Kondisi",
                        "tempC": "Suhu (°C)",
                        "rh": "Kelembapan (%)"
                    })
                    st.success(f"✅ Prakiraan Cuaca: {hasil_display.loc[pilihan,'adm4']} "
                               f"- {hasil_display.loc[pilihan,'adm3']}")
                    st.dataframe(df_cuaca, use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Terjadi kesalahan koneksi: {e}")
