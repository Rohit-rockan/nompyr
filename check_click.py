from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_console(msg):
            print(f"CONSOLE [{msg.type}]: {msg.text}")
        page.on("console", handle_console)
        
        def handle_error(err):
            print(f"PAGE ERROR: {err}")
        page.on("pageerror", handle_error)
        
        try:
            print("Navigating...")
            page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            button = page.locator("button:has-text('Enter the Abyss')")
            if button.count() > 0:
                print("Clicking button...")
                button.click()
                print("Waiting 10 seconds for animation to finish...")
                time.sleep(10)
                print("Done waiting.")
            else:
                print("Button not found")
        except Exception as e:
            print(f"Exception: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
