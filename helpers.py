from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

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