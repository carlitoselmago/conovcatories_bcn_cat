import os
import pdfplumber
import pandas as pd

PDF_FOLDER = "resolucions"      # folder with your PDFs
OUT_FOLDER = "data"    # where to save CSVs

os.makedirs(OUT_FOLDER, exist_ok=True)

def extract_tables_from_pdf(pdf_path, out_folder=OUT_FOLDER):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for i, table in enumerate(tables, start=1):
                # Convert to DataFrame
                df = pd.DataFrame(table)

                # Optional: treat first row as header if it’s actually column names
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)

                out_path = os.path.join(
                    out_folder,
                    f"{pdf_name}_page{page_num}_table{i}.csv"
                )
                df.to_csv(out_path, index=False)
                print(f"Saved {out_path}")

# Loop over all PDFs in the folder
for filename in os.listdir(PDF_FOLDER):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(PDF_FOLDER, filename)
        print(f"Processing {pdf_path}")
        extract_tables_from_pdf(pdf_path)
