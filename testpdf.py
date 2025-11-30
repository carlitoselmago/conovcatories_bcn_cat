from pdf2image import convert_from_path





pdf_path = "resolucions/3866312.pdf"
pages = convert_from_path(pdf_path, dpi=300)
# Save all pages as images
page_images = []
for i, page in enumerate(pages):
    img_path = f"page_{i}.png"
    page.save(img_path, "PNG")
    page_images.append(img_path)

print("pages processed:::")

import layoutparser as lp

# Load a pre-trained table detection model
# Download from https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/blob/d4cebcc544ac0c9899748e1023e2f3ccda8ca70e/model_final.pth?utm_source=chatgpt.com
# https://github.com/Layout-Parser/layout-parser/blob/main/src/layoutparser/models/detectron2/catalog.py
model = lp.Detectron2LayoutModel(
    config_path="config.yml",
    model_path="model_final.pth",
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
)


#Detect tables on each page
import cv2

all_tables = []

for img_path in page_images:
    image = cv2.imread(img_path)
    layout = model.detect(image)

    # Filter only tables
    tables = lp.Layout([b for b in layout if b.type == "Table"])
    print(f"{img_path}: found {len(tables)} tables")

    all_tables.append((img_path, tables))


# OCR
import pytesseract
import pandas as pd

output_tables = []

for img_path, tables in all_tables:
    img = cv2.imread(img_path)

    for idx, table in enumerate(tables):

        # Crop table region
        x1, y1, x2, y2 = map(int, table.coordinates)
        table_img = img[y1:y2, x1:x2]

        # OCR table area
        ocr_text = pytesseract.image_to_string(table_img)

        # Convert OCR text to rows
        rows = [r.strip() for r in ocr_text.split("\n") if r.strip()]

        df = pd.DataFrame({"row": rows})
        output_tables.append(df)

        # Save CSV
        df.to_csv(f"table_{img_path}_#{idx}.csv", index=False)

        print(f"Extracted: table_{img_path}_#{idx}.csv")
