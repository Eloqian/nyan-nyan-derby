from playwright.sync_api import sync_playwright

def verify_i18n():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Visit Home Page (Default: Chinese)
            print("Navigating to home page...")
            page.goto("http://localhost:5173/")
            page.wait_for_load_state("networkidle")

            # Check Chinese text
            print("Checking Chinese text...")
            page.screenshot(path="verification/1_home_zh.png")

            # Check status text (Should be "Ready")
            status_text = page.locator("text=准备开始") # Ready in Chinese
            if status_text.count() > 0:
                print("Status text (ZH) found.")
            else:
                print("Status text (ZH) NOT found.")

            # 2. Switch to English
            print("Switching to English...")
            page.locator(".n-base-selection").click()
            page.get_by_text("English").click()
            page.wait_for_timeout(500)

            print("Checking English text...")
            page.screenshot(path="verification/2_home_en.png")

            # Check status text (Should be "Ready to Start")
            if page.locator("text=Ready to Start").count() > 0:
                print("Status text (EN) found.")

            # 3. Persistence Check
            print("Reloading page to check persistence (should stay English)...")
            page.reload()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)

            page.screenshot(path="verification/3_persistence_en.png")
            if page.locator("text=Meow Meow Cup").count() > 0:
                print("Persistence verified: Still in English.")
            else:
                print("Persistence FAILED: Not in English.")

            # 4. Switch to Japanese
            print("Switching to Japanese...")
            page.locator(".n-base-selection").click()
            page.get_by_text("日本語").click()
            page.wait_for_timeout(500)

            print("Checking Japanese text...")
            page.screenshot(path="verification/4_home_ja.png")

            if page.locator("text=開始準備完了").count() > 0:
                 print("Status text (JA) found.")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_i18n()
