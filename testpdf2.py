import os
import cv2
import base64
from pdf2image import convert_from_path
import layoutparser as lp
from openai import OpenAI
from helpers import Helpers
import csv
H=Helpers()

# =============================
# CONFIG
# =============================

inputfolder="resolucions"
imagefolder="page_images"

# Parse all pdfs recursevelly
for root, dirs, files in os.walk("resolucions"):
    for file in files:
        if file.lower().endswith(".pdf"):

        # Clean up older images
        files = glob.glob(imagefolder+'/*')
        for f in files:
            os.remove(f)




        pdf_path = "resolucions/3866312.pdf"
        images_dir = "page_images"
        os.makedirs(images_dir, exist_ok=True)

        output_dir = "annex_csv"
        os.makedirs(output_dir, exist_ok=True)

        client = OpenAI()

        # 2. Load table detection model
        model = lp.Detectron2LayoutModel(
            config_path="config.yml",
            model_path="model_final.pth",
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        )

        # 3. MAIN EXTRACTION PIPELINE


        annexes = {}  
        current_annex = None

        for img_path in page_images:
            print(f"\n=== Processing {img_path} ===")

            # Load full page and encode
            img = cv2.imread(img_path)
            retval, buffer = cv2.imencode(".png", img)
            b64_page = base64.b64encode(buffer).decode("utf-8")

            # ---- Detect ANNEX
            annex_id = H.detect_annex_id(b64_page)
            if annex_id != "NONE":
                current_annex = annex_id
                if annex_id not in annexes:
                    annexes[annex_id] = {"columns": None, "rows": []}
                print(f"→ Found new annex: {annex_id}")

                # ---- Extract column names on the first page of an annex
                if annexes[annex_id]["columns"] is None:
                    cols = extract_columns_from_page(b64_page)
                    annexes[annex_id]["columns"] = cols
                    print(f"→ Columns for {annex_id}: {cols}")

            # ---- Extract rows for the current annex (multi-page table continues)
            if current_annex:
                cols = annexes[current_annex]["columns"]
                if cols:
                    print(f"→ Extracting rows for {current_annex}…")
                    csv_rows = H.extract_rows_from_page(b64_page, cols)
                    annexes[current_annex]["rows"].append(csv_rows)




        # 4. SAVE ONE CSV PER ANNEX

        for annex_id, data in annexes.items():
            out_path = os.path.join(output_dir, f"{annex_id}.csv")

            with open(out_path, "w", encoding="utf-8") as f:
                # write header
                columns = data["columns"]
                if not columns:
                    print(f"⚠ Annex {annex_id} has no columns, skipping CSV.")
                    continue

                f.write(";".join(columns) + "\n")
                # write rows
                for block in data["rows"]:
                    if not block.strip():
                        continue

                    for line in block.splitlines():
                        stripped = line.strip()
                        if stripped in ("```", "``", "`"):
                            continue
                        if stripped == "":
                            continue
                        f.write(stripped + "\n")

            print(f"✓ Saved CSV for {annex_id} → {out_path}")


        print("\n✓ All annex tables extracted!")
