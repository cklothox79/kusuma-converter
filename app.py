import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter
from docx import Document
import io

st.title("📂 Kusuma Converter")
st.write("Konversi file antara **Excel, CSV, Word, dan PDF**")

# Upload file
uploaded_file = st.file_uploader("Upload file", type=["xlsx", "csv", "docx"])

# Pilihan format output
output_format = st.selectbox("Pilih format output", ["CSV", "Excel", "Word", "PDF"])

def df_to_pdf(df):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    table = Table([df.columns.tolist()] + df.values.tolist())
    doc.build([table])
    pdf_buffer.seek(0)
    return pdf_buffer

def df_to_word(df):
    buffer = io.BytesIO()
    doc = Document()
    table = doc.add_table(rows=1, cols=len(df.columns))

    # Header
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr_cells[i].text = str(col)

    # Data
    for row in df.values.tolist():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].text = str(val)

    doc.save(buffer)
    buffer.seek(0)
    return buffer

if uploaded_file:
    filename = uploaded_file.name

    # Baca file ke DataFrame
    if filename.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif filename.endswith(".docx"):
        doc = Document(uploaded_file)
        data = []
        for table in doc.tables:
            for row in table.rows:
                data.append([cell.text for cell in row.cells])
        df = pd.DataFrame(data[1:], columns=data[0]) if data else pd.DataFrame()
    else:
        st.error("Format file belum didukung")
        df = None

    if df is not None and not df.empty:
        st.subheader("Preview Data")
        st.dataframe(df.head())

        if output_format == "CSV":
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv_data, "output.csv", "text/csv")

        elif output_format == "Excel":
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, engine="openpyxl")
            towrite.seek(0)
            st.download_button("⬇️ Download Excel", towrite, "output.xlsx")

        elif output_format == "Word":
            word_buffer = df_to_word(df)
            st.download_button("⬇️ Download Word", word_buffer, "output.docx")

        elif output_format == "PDF":
            pdf_buffer = df_to_pdf(df)
            st.download_button("⬇️ Download PDF", pdf_buffer, "output.pdf", "application/pdf")
    else:
        st.warning("Data kosong atau tidak terbaca.")
