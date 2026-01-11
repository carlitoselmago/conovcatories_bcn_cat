import sys
print("DEBUG: script started", flush=True)

try:
    import undetected_chromedriver as uc
    print("DEBUG: imported undetected_chromedriver", flush=True)

    from selenium_stealth import stealth
    print("DEBUG: imported selenium_stealth", flush=True)

    print("DEBUG: building Chrome options", flush=True)

    options = uc.ChromeOptions()
    options.headless = False  # MUST be visible

    # --- Linux stability flags ---
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    # Reduce automation fingerprints
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    print("DEBUG: launching Chrome", flush=True)

    driver = uc.Chrome(
        options=options,
        use_subprocess=False
    )

    print("DEBUG: Chrome launched", flush=True)

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    print("DEBUG: stealth applied", flush=True)

    print("DEBUG: opening https://artfacts.net", flush=True)
    driver.get("https://artfacts.net")

    print("\nIf a Cloudflare captcha appears:")
    print("• solve it manually")
    print("• wait until the homepage content loads")
    print("• do NOT refresh\n")

    input("Press ENTER only AFTER the page looks normal...")

    print("\nDEBUG: after solve")
    print("URL:", driver.current_url)
    print("Title:", driver.title)

    input("\nPress ENTER to close the browser.")
    driver.quit()

except Exception as e:
    print("\nFATAL ERROR:", e, flush=True)
    sys.exit(1)
