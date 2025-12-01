from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
import requests
import difflib

class parser():

    name = "artfacts"

    def __init__(self):
        options = Options()
        options.headless = True  # set to False to see the browser
        self.driver = webdriver.Firefox(options=options)

    def parseURL(self, url):
        return self.get_page(url)

    def findArtist(self, name):
        # Build URL
        query = name.replace(" ", "%20")
        url = f"https://artfacts.net/api/v0/search?q={query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://artfacts.net/",
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            print("⚠ Connection error:", e)
            return None

        # --- Try to parse JSON safely ---
        try:
            data = r.json()
        except Exception:
            print("⚠ API returned non-JSON response:")
            print("Status:", r.status_code)
            print("Body preview:", r.text[:500])
            return None

        # If no results
        if data.get("total", 0) == 0:
            return None

        results = data.get("results", [])

        # Prepare name variants
        input_variants = [
            name.lower().strip(),
            " ".join(reversed(name.lower().split()))
        ]

        best = None
        best_score = 0.0

        for item in results:
            cand = item.get("name", "").lower().strip()
            cand_variants = [cand, " ".join(reversed(cand.split()))]

            score = max(
                difflib.SequenceMatcher(None, iv, cv).ratio()
                for iv in input_variants
                for cv in cand_variants
            )

            if score > best_score:
                best_score = score
                best = item

        if best_score < 0.6:
            return None

        return best

    def get_artist(self, name):

        # 1. Search artist in API
        res = self.findArtist(name)
        
        if not res:
            print(f"[!] No API match found for: {name}")
            return None

        # 2. Get URL from the match
        url = self.get_artisturl(res)
        if not url:
            print(f"[!] Could not build profile URL for: {name}")
            return res  # return only the API data

        # 3. Parse artist page with Selenium
        artistdetails = self.parseURL(url)
        
        if not isinstance(artistdetails, dict):
            print(f"[!] Could not parse artist page for: {name}")
            return res  # return API data only

        # 4. Merge API data with parsed details
        res.update(artistdetails)

        # 5. Return full artist profile
        return res


    def get_artisturl(self,res):
        if res:
            url="https://artfacts.net"+res["links"]["card"]
            return url

        return None

    def get_page(self, url):

        self.driver.get(url)
        time.sleep(3)

        # --- RANKING ---
        try:
            ranking_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__ranking"
            )
            title = ranking_block.find_element(By.TAG_NAME, "h5").text.strip()
            a_tag = ranking_block.find_element(By.TAG_NAME, "a")
            full_text = a_tag.text.strip()
            scope = a_tag.find_element(By.TAG_NAME, "em").text.strip()
            rank = full_text.replace(scope, "").strip()
        except:
            rank = None
            scope = None

        # --- EXHIBITIONS ---
        try:
            exhibitions_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__exhibitions"
            )
            ex_count = exhibitions_block.find_element(By.TAG_NAME, "a").text.strip()
        except:
            ex_count = None

        # --- GENDER ---
        try:
            gender_value = self.driver.find_element(
                By.XPATH,
                "//tr[td[normalize-space()='Gender']]//a"
            ).text.strip()
        except:
            gender_value = None

        # --- SAFELY RETURN ALL FIELDS ---
        return {
            "rank": rank,
            "scope": scope,
            "exhibitions": ex_count,
            "gender": gender_value,
        }

            

 
