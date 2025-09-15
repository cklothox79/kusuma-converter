import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

st.markdown("<h2 style='text-align:center; color:#4CAF50;'>📂 Kusuma Converter</h2>", unsafe_allow_html=True)
st.write("Konversi file **Excel, CSV, Word, dan PDF** dengan mudah dan cepat ⚡")

uploaded_file = st.file_uploader("📤 Upload file", type=["xlsx", "csv", "docx", "pdf"])
output_format = st.selectbox("Pilih format output:", ["Excel (XLSX)", "CSV", "Word (DOCX)", "PDF"])

def convert_excel_csv(file, to_format):
    df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
    buf = BytesIO()
    if to_format == "Excel (XLSX)":
        df.to_excel(buf, index=False)
    else:
        df.to_csv(buf, index=False)
    buf.seek(0)
    return buf

def convert_word_to_pdf(file):
    doc = Document(file)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            c.drawString(50, y, text)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
    c.save()
    buffer.seek(0)
    return buffer

if uploaded_file and output_format:
    if st.button("🔄 Convert"):
        with st.spinner("Sedang mengonversi..."):
            result_file = None

            if uploaded_file.name.endswith(("xlsx", "csv")) and output_format in ["Excel (XLSX)", "CSV"]:
                result_file = convert_excel_csv(uploaded_file, output_format)

            elif uploaded_file.name.endswith("docx") and output_format == "PDF":
                result_file = convert_word_to_pdf(uploaded_file)

            if result_file:
                ext = "xlsx" if output_format == "Excel (XLSX)" else \
                      "csv" if output_format == "CSV" else \
                      "docx" if output_format == "Word (DOCX)" else "pdf"

                st.success("✅ Konversi selesai! Silakan unduh file hasil.")
                st.download_button("📥 Download File", data=result_file, file_name=f"converted.{ext}")
            else:
                st.error("❌ Format input dan output tidak cocok atau belum didukung.")
