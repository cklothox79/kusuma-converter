import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
import os

# ==== Judul Aplikasi ====
st.markdown("<h2 style='text-align:center; color:#4CAF50;'>📂 Kusuma Converter</h2>", unsafe_allow_html=True)
st.write("Konversi file **Excel, CSV, Word, dan PDF** dengan mudah dan cepat ⚡")

# ==== Upload File ====
uploaded_file = st.file_uploader("📤 Upload file", type=["xlsx", "csv", "docx", "pdf"])

# ==== Pilihan Format Output ====
output_format = st.selectbox("Pilih format output:", ["Excel (XLSX)", "CSV", "Word (DOCX)", "PDF"])

# ==== Fungsi Konversi ====
def convert_excel_csv(file, to_format):
    df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
    buf = BytesIO()
    if to_format == "Excel (XLSX)":
        df.to_excel(buf, index=False)
    else:
        df.to_csv(buf, index=False)
    buf.seek(0)
    return buf

def convert_word_pdf(file, to_format):
    # DOCX <-> PDF (hanya Windows / butuh pandoc di Linux)
    input_path = f"temp_input.{file.name.split('.')[-1]}"
    output_path = f"temp_output.{ 'pdf' if to_format=='PDF' else 'docx' }"

    with open(input_path, "wb") as f:
        f.write(file.getbuffer())

    if to_format == "PDF":
        try:
            import docx2pdf
            docx2pdf.convert(input_path, output_path)
        except Exception:
            st.error("Konversi Word ke PDF membutuhkan Windows atau pandoc.")
            return None
    else:  # PDF ke Word
        try:
            import pypandoc
            pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
        except Exception:
            st.error("Konversi PDF ke Word membutuhkan pandoc.")
            return None

    with open(output_path, "rb") as f:
        result = BytesIO(f.read())

    os.remove(input_path)
    os.remove(output_path)
    result.seek(0)
    return result

# ==== Proses Konversi ====
if uploaded_file and output_format:
    if st.button("🔄 Convert"):
        with st.spinner("Sedang mengonversi..."):
            result_file = None

            # Excel <-> CSV
            if uploaded_file.name.endswith(("xlsx", "csv")):
                if output_format in ["Excel (XLSX)", "CSV"]:
                    result_file = convert_excel_csv(uploaded_file, output_format)

            # Word <-> PDF
            elif uploaded_file.name.endswith(("docx", "pdf")):
                if output_format in ["Word (DOCX)", "PDF"]:
                    result_file = convert_word_pdf(uploaded_file, output_format)

            if result_file:
                ext = "xlsx" if output_format == "Excel (XLSX)" else \
                      "csv" if output_format == "CSV" else \
                      "docx" if output_format == "Word (DOCX)" else "pdf"

                st.success("✅ Konversi selesai! Silakan unduh file hasil.")
                st.download_button("📥 Download File", data=result_file, file_name=f"converted.{ext}")
            else:
                st.error("❌ Format input dan output tidak cocok atau library pendukung belum tersedia.")
