import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🌦️ Prakiraan Cuaca BMKG", page_icon="🌦️", layout="centered")
st.title("🌦️ Prakiraan Cuaca BMKG by Nama Daerah")

# === 1. Input Nama Daerah ===
nama_daerah = st.text_input("Masukkan nama daerah (Provinsi/Kabupaten/Kecamatan/Desa):", "Simogirang")

if st.button("Cari Prakiraan Cuaca"):
    if not nama_daerah.strip():
        st.warning("Silakan masukkan nama daerah terlebih dahulu.")
    else:
        try:
            # === 2. Cari ID Wilayah (adm4) ===
            st.write(f"🔍 Mencari wilayah dengan kata kunci: **{nama_daerah}** ...")
            search_url = f"https://api-apps.bmkg.go.id/publik/prakiraan-cuaca/wilayah?nama={nama_daerah}&level=adm4"
            resp = requests.get(search_url, timeout=15)
            resp.raise_for_status()
            hasil = resp.json()

            if not hasil.get("data"):
                st.error("❌ Wilayah tidak ditemukan. Coba nama lain (misal: 'Prambon', 'Sidoarjo').")
            else:
                # Tampilkan daftar hasil pencarian
                wilayah_df = pd.DataFrame(hasil["data"])
                wilayah_df_display = wilayah_df[["adm1", "adm2", "adm3", "adm4", "id"]]
                st.dataframe(wilayah_df_display, use_container_width=True)

                # === 3. Pilih Wilayah Jika Banyak ===
                pilihan = st.selectbox("Pilih Wilayah:", 
                                       wilayah_df_display.index,
                                       format_func=lambda i: f"{wilayah_df_display.loc[i,'adm4']} - "
                                                             f"{wilayah_df_display.loc[i,'adm3']} - "
                                                             f"{wilayah_df_display.loc[i,'adm2']} - "
                                                             f"{wilayah_df_display.loc[i,'adm1']}")
                wilayah_id = wilayah_df_display.loc[pilihan, "id"]

                # === 4. Ambil Prakiraan Cuaca ===
                cuaca_url = f"https://api-apps.bmkg.go.id/publik/prakiraan-cuaca?adm4={wilayah_id}"
                st.write(f"🌐 Mengambil prakiraan cuaca untuk ID: `{wilayah_id}` ...")
                cuaca_resp = requests.get(cuaca_url, timeout=15)
                cuaca_resp.raise_for_status()
                cuaca_data = cuaca_resp.json()

                if "data" not in cuaca_data or not cuaca_data["data"]:
                    st.error("❌ Tidak ada data prakiraan cuaca.")
                else:
                    df_cuaca = pd.DataFrame(cuaca_data["data"][0]["cuaca"])
                    # Rapikan nama kolom
                    df_cuaca = df_cuaca.rename(columns={
                        "jamCuaca": "Jam",
                        "kodeCuaca": "Kode",
                        "cuaca": "Kondisi",
                        "tempC": "Suhu (°C)",
                        "rh": "Kelembapan (%)"
                    })
                    st.success(f"✅ Prakiraan Cuaca: {wilayah_df_display.loc[pilihan,'adm4']} "
                               f"- {wilayah_df_display.loc[pilihan,'adm3']}")
                    st.dataframe(df_cuaca, use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Terjadi kesalahan koneksi: {e}")
