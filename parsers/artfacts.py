import difflib

import undetected_chromedriver as uc
from selenium_stealth import stealth

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

class parser():

    name = "artfacts"

    def __init__(self):
        # -------------------------------
        # Chrome options
        # -------------------------------
        options = uc.ChromeOptions()
        options.headless = False  # MUST be visible (captcha)

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.6167.140 Safari/537.36"
        )
        options.add_argument(f"--user-agent={user_agent}")

        self.driver = uc.Chrome(
            options=options,
            use_subprocess=False
        )

        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        self._bootstrap_browser()

    # ---------------------------------------------------------
    # INITIAL CAPTCHA BOOTSTRAP
    # ---------------------------------------------------------
    def _bootstrap_browser(self):
        self.driver.get("https://artfacts.net")
        input("If a Cloudflare captcha appears, solve it now, then press ENTER...")

    # ---------------------------------------------------------
    # SELENIUM REPLACEMENT FOR API SEARCH
    # ---------------------------------------------------------
    def findArtist(self, name):
        query = name.replace(" ", "%20")
        url =  f"https://artfacts.net/api/v0/search?q={query}"

        self.driver.get(url)
        
        pre = self.driver.find_element(By.TAG_NAME, "pre").text
        data = json.loads(pre)

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

    # ---------------------------------------------------------
    # MAIN ENTRY POINT (UNCHANGED LOGIC)
    # ---------------------------------------------------------
    def get_artist(self, name):
        res = self.findArtist(name)

        if not res:
            print(f"[!] No match found for: {name}")
            return None

        url = self.get_artisturl(res)
        if not url:
            return res

        if "/ehibition" not in url:
            artistdetails = self.get_page(url)
            if isinstance(artistdetails, dict):
                res.update(artistdetails)

            return res
        else:
            return None

    # ---------------------------------------------------------
    # BUILD ARTIST URL (UNCHANGED)
    # ---------------------------------------------------------
    def get_artisturl(self, res):
        if res:
            return "https://artfacts.net" + res["links"]["card"]
        return None

    # ---------------------------------------------------------
    # PARSE ARTIST PAGE (UNCHANGED)
    # ---------------------------------------------------------
    def get_page(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 30)

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "div.app-js-styles-shared-ScrollContainer__ranking")
                )
            )
        except TimeoutException:
            return None

        # --- RANKING ---
        try:
            ranking_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__ranking"
            )
            a = ranking_block.find_element(By.TAG_NAME, "a")
            scope = a.find_element(By.TAG_NAME, "em").text.strip()
            rank = a.text.replace(scope, "").strip()
        except Exception:
            rank = None
            scope = None

        # --- EXHIBITIONS ---
        try:
            ex_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__exhibitions"
            )
            exhibitions = ex_block.find_element(
                By.TAG_NAME, "a"
            ).text.strip()
        except Exception:
            exhibitions = None

        # --- GENDER ---
        try:
            gender = self.driver.find_element(
                By.XPATH,
                "//tr[td[normalize-space()='Gender']]//a"
            ).text.strip()
        except Exception:
            gender = None

        return {
            "rank": rank,
            "scope": scope,
            "exhibitions": exhibitions,
            "gender": gender,
        }
