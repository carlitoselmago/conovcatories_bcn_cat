from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time

class parser():

    name = "artfacts"

    def __init__(self):
        options = Options()
        options.headless = True  # set to False to see the browser
        self.driver = webdriver.Firefox(options=options)

    def parseURL(self, url):
        self.get_page(url)

    def get_page(self, url):

        self.driver.get(url)
        time.sleep(3)  # Let JS load

        print("\n=== PAGE TITLE ===")
        print(self.driver.title)


        # -----------------------------------------
        # EXTRACT RANKING BLOCK (your requested part)
        # -----------------------------------------
        try:
            # 1. Find the Ranking container (using the class you showed)
            ranking_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__ranking"
            )

            # 2. Extract the <h5> title
            title = ranking_block.find_element(By.TAG_NAME, "h5").text.strip()

            # 3. Extract the <a> with rank info
            a_tag = ranking_block.find_element(By.TAG_NAME, "a")

            full_text = a_tag.text.strip()

            # 4. Extract the <em> element
            scope = a_tag.find_element(By.TAG_NAME, "em").text.strip()

            # 5. Rank number = full_text minus scope
            rank = full_text.replace(scope, "").strip()

            print("\n=== RANKING FOUND ===")
            print("Title:", title)
            print("Rank:", rank)
            print("Scope:", scope)

        except Exception as e:
            print("\n[!] Could not extract ranking:", e)

        # -----------------------------------------

        # -----------------------------------------
        # EXTRACT VERIFIED EXHIBITIONS
        # -----------------------------------------
        try:
            exhibitions_block = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.app-js-styles-shared-ScrollContainer__exhibitions"
            )

            # Extract the title <h5>
            ex_title = exhibitions_block.find_element(By.TAG_NAME, "h5").text.strip()

            # Extract the <a> text — this is the number of exhibitions
            ex_count = exhibitions_block.find_element(By.TAG_NAME, "a").text.strip()

            print("\n=== VERIFIED EXHIBITIONS ===")
            print("Title:", ex_title)
            print("Count:", ex_count)

            

        except Exception as e:
            print("\n[!] Could not extract exhibitions:", e)
        self.driver.quit()
