from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pdf2image import convert_from_path
import pandas as pd
import numpy as np
import torch
import os
import re

class Helpers:

    def __init__(self):
        print("Started Helper class")

    

    def init_genderClass(self):
        model_name = "padmajabfrl/Gender-Classification"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def predictGender(self, name):
        inputs = self.tokenizer(name, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=-1)
        predicted_idx = int(torch.argmax(probs))

        return {
            "label": self.model.config.id2label[predicted_idx],
            "score": float(probs[0][predicted_idx]),
        }
        
    def reorder_with_map(self,values, mapping):
        # Determine result length
        size = max(mapping.values()) + 1
        result = [None] * size

        for old_index, new_index in mapping.items():
            if old_index < len(values):   # check index is valid
                result[new_index] = values[old_index]

        return result

    def cleanup_number(self,n):
        if n is None:
            return None

        try:
            s = str(n)

            # 1) Remove currency and whitespace
            s = s.replace("€", "").replace(" ", "")

            # 2) Remove ANYTHING that is NOT digit, dot or comma
            # This kills "000 ,", ",", ".", ".,", ",,", etc
            s = re.sub(r"[^0-9.,]", "", s)

            # 3) If the string has no digits at all, return None
            if not re.search(r"\d", s):
                return None

            # 4) Remove isolated commas/dots at the end or beginning
            #    e.g. "000," -> "000", "000." -> "000"
            s = s.strip(".,")   

            # 5) Now remove thousands separators
            s = s.replace(".", "")

            # 6) Convert decimal comma to dot
            s = s.replace(",", ".")

            # 7) Final cleanup: if it ends with a dot: "123." → "123"
            if s.endswith("."):
                s = s[:-1]

            return float(s)

        except Exception as e:
            print("ERROR converting:", n, "=>", e)
            return None
    

    def cleanup_punts(self,n):
        if n:
            if n[-1]==",":

                n=n[0]+","+n[1:100].replace(",","")
            
        return n

    def numeric_sort_key(self,fname):
        m = re.search(r"page_(\d+)\.png", fname)
        if m:
            return int(m.group(1))
        return 999999  # fallback
        

    def pdf_to_images(self,images_dir,pdf_path):
        print("Checking if pages already converted…")

        # Check if any PNG files exist
        existing = sorted(
            [f for f in os.listdir(images_dir) if f.lower().endswith(".png")],
            key=self.numeric_sort_key
        )
        if existing:
            print(f"✓ Found {len(existing)} existing PNG pages — skipping conversion.")
            return [os.path.join(images_dir, f) for f in existing]

        print("→ No images found. Converting PDF…")

        pages = convert_from_path(pdf_path, dpi=300)
        #pages = convert_from_path(pdf_path, dpi=400)
        page_images = []

        for i, page in enumerate(pages):
            img_path = os.path.join(images_dir, f"page_{i}.png")
            page.save(img_path, "PNG")
            page_images.append(img_path)

        print("✓ PDF converted to images")
        return page_images




    def extract_text_from_gpt(self,client,messages):
            """Unified way to call GPT and extract only text parts."""
            model="gpt-5-mini"#"gpt-4o-mini"

            
            if model=="gpt-5-mini":
                    response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=4096
                )
            else:
                response = client.chat.completions.create(
                    model=model,
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

    def detect_annex_id(self,client,b64_page):
        """Returns ANNEX number or NONE."""
        text = self.extract_text_from_gpt(client,[
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

    def extract_rows_from_page(self,client,b64_page, columns):
        """Extract CSV rows using known column names. Cleans markdown artifacts."""
        prompt = f"""
            Extract all table rows from this page using these column names:
            {columns}

            Output ONLY CSV rows using ';' as separator.
            Do NOT output the header.
            Do NOT include commentary.
            """

        raw = self.extract_text_from_gpt(client,[
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

    def extract_columns_from_page(self,client,b64_page):
        """Extract header columns for the first page of an annex (robust)."""
        import json
        raw = self.extract_text_from_gpt(client,[
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

    def is_mostly_numeric(self,s):
        if pd.isna(s):
            return False
        s = str(s).strip()

        # Keep letters: if there is at least 1 letter, it's NOT numeric
        if re.search(r"[a-zA-Zà-ÿÀ-Ÿ]", s):
            return False
        
        # If removing digits and common separators leaves nothing → numeric-like
        cleaned = re.sub(r"[0-9\s/.,:-]", "", s)
        return cleaned == ""