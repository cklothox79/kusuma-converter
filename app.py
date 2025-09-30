import streamlit as st
import pandas as pd
import difflib

st.set_page_config(page_title="Converter Kode Wilayah", layout="centered")

@st.cache_data
def load_kode_wilayah():
    df = pd.read_csv("data/kode_wilayah_split.csv", dtype=str)

    # --- fungsi normalisasi teks ---
    def normalisasi(teks: str) -> str:
        if pd.isna(teks):
            return ""
        return (
            str(teks)
            .strip()
            .lower()
            .replace("-", " ")
            .replace(".", "")
            .replace(",", "")
        )

    # Normalisasi tiap kolom penting
    for col in ["propinsi", "kabupaten", "kecamatan", "desa"]:
        df[col] = df[col].apply(normalisasi)

    # Gabungkan semua nama wilayah jadi satu kolom
    df["nama_gabungan"] = (
        df["desa"] + " " +
        df["kecamatan"] + " " +
        df["kabupaten"] + " " +
        df["propinsi"]
    )

    return df

# --- Load data ---
kode_df = load_kode_wilayah()

st.title("🔍 Converter Nama Wilayah → Kode BPS")

# --- Input dari user ---
lokasi = st.text_input("Masukkan nama desa/kecamatan/kabupaten/propinsi:")

def normalisasi_input(teks: str) -> str:
    return (
        str(teks)
        .strip()
        .lower()
        .replace("-", " ")
        .replace(".", "")
        .replace(",", "")
    )

if lokasi:
    user_input = normalisasi_input(lokasi)

    # Ambil semua kandidat dari CSV
    candidates = kode_df["nama_gabungan"].tolist()

    # Cari kemiripan string
    best_match = difflib.get_close_matches(user_input, candidates, n=1, cutoff=0.6)

    if best_match:
        row = kode_df[kode_df["nama_gabungan"] == best_match[0]].iloc[0]
        kode = row["kode"]
        nama_res = row["desa"] if row["desa"] else row["kecamatan"]
        st.success(f"✅ Kode Wilayah: {kode} ({nama_res})")
    else:
        st.warning("⚠️ Kode wilayah tidak ditemukan di CSV (coba perbaiki input)")

# --- Info tambahan ---
with st.expander("ℹ️ Cara pakai"):
    st.write("""
    - Ketik nama desa, kecamatan, kabupaten, atau provinsi  
    - Contoh: `Kesambi`, `Sidoarjo`, `Limboto Barat`  
    - Toleran dengan salah ketik kecil (misal `Sidoarjoo` tetap ketemu `Sidoarjo`)
    """)
