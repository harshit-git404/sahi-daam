import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from commodity_rules import COMMODITY_RULES, normalize_quantity, classify_variants

def run_headless():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            for commodity_id, rules in COMMODITY_RULES.items():
                search_term = rules["search_term"]
                print(f"Testing {commodity_id} headless...")
                page.goto(f"https://blinkit.com/s/?q={search_term}", timeout=30000)
                time.sleep(5)
                product_cards = page.locator("a[data-test-id='plp-product']").all()
                if not product_cards:
                    product_cards = page.locator("div").filter(has_text="ADD").all()

                count = len(product_cards)
                print(f"Got {count} products for {commodity_id}")
                if count > 0:
                    text = product_cards[0].inner_text()
                    print(f"First product text:\n{text}\n")
                    
        except Exception as e:
            print(f"Error: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_headless()
