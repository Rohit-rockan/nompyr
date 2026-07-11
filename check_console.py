from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Navigating to http://localhost:3000...")
            page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3) # Wait for React to render
            print("Navigation complete. Checking elements...")
            
            button = page.locator("button:has-text('Enter the Abyss')")
            if button.count() > 0:
                print("Button found! Is it visible? ", button.is_visible())
            else:
                print("Button 'Enter the Abyss' NOT found in DOM.")
                print("Dumping body innerHTML snippet:")
                print(page.evaluate("document.body.innerHTML").strip()[:1500])
        except Exception as e:
            print(f"Exception: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
