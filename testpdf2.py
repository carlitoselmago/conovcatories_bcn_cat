import os
import cv2
import base64
from pdf2image import convert_from_path
import layoutparser as lp
from openai import OpenAI


# =============================
# CONFIG
# =============================
pdf_path = "resolucions/3866312.pdf"
images_dir = "page_images"
os.makedirs(images_dir, exist_ok=True)

output_dir = "annex_csv"
os.makedirs(output_dir, exist_ok=True)

client = OpenAI()


# =============================
# 1. Convert PDF → images (only if images don't already exist)
# =============================

def pdf_to_images(pdf_path):
    print("Checking if pages already converted…")

    # Check if any PNG files exist
    existing = sorted(
        [f for f in os.listdir(images_dir) if f.lower().endswith(".png")]
    )
    if existing:
        print(f"✓ Found {len(existing)} existing PNG pages — skipping conversion.")
        return [os.path.join(images_dir, f) for f in existing]

    print("→ No images found. Converting PDF…")

    pages = convert_from_path(pdf_path, dpi=300)
    page_images = []

    for i, page in enumerate(pages):
        img_path = os.path.join(images_dir, f"page_{i}.png")
        page.save(img_path, "PNG")
        page_images.append(img_path)

    print("✓ PDF converted to images")
    return page_images


page_images = pdf_to_images(pdf_path)



# =============================
# 2. Load table detection model
# =============================

model = lp.Detectron2LayoutModel(
    config_path="config.yml",
    model_path="model_final.pth",
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
)


# =============================
# OCR HELPERS USING GPT-4o-mini
# =============================

def extract_text_from_gpt(messages):
    """Unified way to call GPT and extract only text parts."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=4096
    )
    msg = response.choices[0].message

    if isinstance(msg.content, str):
        return msg.content

    return "".join(
        part.text for part in msg.content
        if getattr(part, "type", None) == "text"
    )


def detect_annex_id(b64_page):
    """Returns ANNEX number or NONE."""
    text = extract_text_from_gpt([
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "Does this page contain an ANNEX label (e.g., 'ANNEX 1', 'ANNEX 2')? "
                         "Return ONLY the annex name, or 'NONE' if not found."},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64_page}"}}
            ]
        }
    ])
    return text.strip()


def extract_columns_from_page(b64_page):
    """Extract header columns for the first page of an annex (robust)."""
    import json
    raw = extract_text_from_gpt([
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "Extract ONLY the column names from the table on this page. "
                         "Return them as a JSON list of strings. No commentary."},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64_page}"}}
            ]
        }
    ])

    cleaned = raw.strip()

    # Remove fences like ```json or ``` or ```.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # Remove language identifier if present
        cleaned = cleaned.replace("json", "", 1).strip()

    # Try JSON parsing
    try:
        cols = json.loads(cleaned)
        if isinstance(cols, list):
            return cols
    except Exception as e:
        print("⚠ JSON parsing failed:", e)

    # LAST RESORT:
    # attempt to extract quoted strings manually
    import re
    matches = re.findall(r'"(.*?)"', cleaned)
    if matches:
        print("✓ Recovered column names by fallback:", matches)
        return matches

    print("⚠ Could not interpret column JSON, raw text:", raw)
    return None



def extract_rows_from_page(b64_page, columns):
    """Extract CSV rows using known column names. Cleans markdown artifacts."""
    prompt = f"""
        Extract all table rows from this page using these column names:
        {columns}

        Output ONLY CSV rows using ';' as separator.
        Do NOT output the header.
        Do NOT include commentary.
        """

    raw = extract_text_from_gpt([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_page}"}}
            ]
        }
    ]).strip()

    # --- CLEANING ---
    cleaned_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped in ("```", "``", "`"):
            continue
        if not stripped:
            continue
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)



# =============================
# 3. MAIN EXTRACTION PIPELINE
# =============================

annexes = {}   # { "ANNEX 1": {"columns": [...], "rows": [...] } }
current_annex = None

for img_path in page_images:
    print(f"\n=== Processing {img_path} ===")

    # Load full page and encode
    img = cv2.imread(img_path)
    retval, buffer = cv2.imencode(".png", img)
    b64_page = base64.b64encode(buffer).decode("utf-8")

    # ---- Detect ANNEX
    annex_id = detect_annex_id(b64_page)
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
            csv_rows = extract_rows_from_page(b64_page, cols)
            annexes[current_annex]["rows"].append(csv_rows)



# =============================
# 4. SAVE ONE CSV PER ANNEX
# =============================

import csv

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
