import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure") and getattr(sys.stdout, "encoding", "") != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from commodity_rules import COMMODITY_RULES, classify_variants, normalize_quantity
except ImportError:
    from experiments.commodity_rules import COMMODITY_RULES, classify_variants, normalize_quantity

LOCATION = "Katpadi, Vellore"
OUTPUT_DIR = BASE_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
CLEAN_DIR = OUTPUT_DIR / "clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def parse_card_lines(lines: list, rules: dict) -> dict:
    """
    Parses inner text lines from a Zepto product card.
    """
    cleaned_lines = [
        line.replace("â‚¹", "₹").replace("Ã¢â€šÂ¹", "₹").replace("Rs.", "₹").replace("Rs ", "₹").strip()
        for line in lines
        if line.strip()
    ]
    
    product = {
        "name": "Unknown",
        "quantity": "Unknown",
        "price": None,
        "mrp": None,
        "raw_text": lines
    }
    
    # Extract prices
    prices = []
    for line in cleaned_lines:
        lower = line.lower()
        if "₹" in line:
            # Avoid lines like '₹24 OFF' or '40% OFF'
            if "off" in lower:
                continue
            nums = re.findall(r"\d+(?:\.\d+)?", line)
            for n in nums:
                try:
                    prices.append(float(n))
                except ValueError:
                    pass
                    
    if prices:
        product["price"] = prices[0]
        if len(prices) > 1:
            product["mrp"] = prices[1]
            
    # Extract name and quantity
    for line in cleaned_lines:
        lower = line.lower()
        if lower in ["add", "off", "out of stock", "in stock", "notify me"] or "₹" in line or "% off" in lower:
            continue
            
        # Quantity patterns
        if re.search(r'\b(?:\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?\s*)?(?:kg|kgs|g|gm|grams|pc|pcs|piece|pieces|bunch|pack))\b', lower):
            if product["quantity"] == "Unknown":
                product["quantity"] = line
        # Commodity name check
        elif len(line) > 2 and len(line) < 100:
            if any(kw in lower for kw in rules["keywords"]) or any(
                kw in lower for kw in ["tomato", "potato", "onion", "carrot", "cucumber", "brinjal", "cauliflower", "cabbage", "banana", "papaya"]
            ):
                if product["name"] == "Unknown":
                    product["name"] = line
            elif product["name"] == "Unknown" and not re.search(r'^\d', line):
                product["name"] = line
                
    return product


def run():
    print("========================================")
    print("ZEPTO SCRAPER PROOF OF CONCEPT")
    print("========================================")
    
    run_summaries = {}
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Navigating to Zepto...")
            page.goto("https://www.zepto.com/", timeout=45000)
            time.sleep(3)
            
            print(f"\n[!] ACTION REQUIRED IN BROWSER [!]")
            print(f"Zepto usually prompts for a delivery location.")
            print(f"Target location: {LOCATION}")
            print("Attempting automated location setup, or you can manually adjust in the browser...")
            
            # Automated location setting attempt
            try:
                select_loc_btn = page.locator("button").filter(has_text="Select Location").first
                if select_loc_btn.count() > 0 and select_loc_btn.is_visible():
                    select_loc_btn.click()
                    time.sleep(2)
                    search_input = page.locator("input[placeholder*='Search'], input[placeholder*='address']").first
                    if search_input.count() > 0:
                        search_input.fill(LOCATION)
                        time.sleep(3)
                        # Click suggestion via JS
                        page.evaluate("""() => {
                            const all = document.querySelectorAll('*');
                            for (const el of all) {
                                if ((el.textContent.includes('Katpadi') || el.textContent.includes('Vellore')) && el.children.length === 0) {
                                    el.click();
                                    if (el.parentElement) el.parentElement.click();
                                    break;
                                }
                            }
                        }""")
                        time.sleep(3)
            except Exception as loc_err:
                print(f"Automated location setup notice: {loc_err}")
                
            print("Waiting up to 30 seconds for location/search bar to become ready...")
            try:
                page.wait_for_selector("header, a[href*='search'], input[placeholder*='Search']", timeout=30000)
            except Exception:
                pass
                
            print("\nStarting multi-commodity extraction...\n")
            
            for commodity_id, rules in COMMODITY_RULES.items():
                search_term = rules["search_term"]
                print(f"--- Processing {commodity_id.upper()} ---")
                
                try:
                    # Navigate directly to search page for the commodity
                    search_url = f"https://www.zepto.com/search?query={search_term}"
                    page.goto(search_url, timeout=30000)
                    
                    # Wait for results to load
                    time.sleep(4)
                    
                    product_cards = page.locator("a[data-testid='product-card'], [data-testid*='product-card'], div[data-testid*='product'], a[href*='/pn/']").all()
                    if not product_cards:
                        product_cards = page.locator("div").filter(has_text="ADD").all()
                        
                    extracted_products = []
                    for card in product_cards:
                        try:
                            text = card.inner_text().strip()
                            if not text:
                                continue
                            
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            product = parse_card_lines(lines, rules)
                            extracted_products.append(product)
                        except Exception:
                            pass
                            
                    # Save raw output
                    raw_output = {
                        "platform": "zepto",
                        "commodity_search": search_term,
                        "location": LOCATION,
                        "collected_at": datetime.now().isoformat(),
                        "products": extracted_products
                    }
                    raw_path = RAW_DIR / f"zepto_{commodity_id}_raw.json"
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(raw_output, f, indent=2, ensure_ascii=False)
                        
                    # Deduplication
                    unique_products = []
                    seen = set()
                    for p_raw in extracted_products:
                        name = p_raw.get("name", "").strip().lower()
                        qty = p_raw.get("quantity", "").strip().lower()
                        price = p_raw.get("price")
                        key = (name, qty, price)
                        if key not in seen:
                            seen.add(key)
                            unique_products.append(p_raw)
                            
                    # Filtering and Classification
                    valid_products = []
                    excluded_products = []
                    
                    for p_unique in unique_products:
                        name = p_unique.get("name", "").strip()
                        name_lower = name.lower()
                        
                        # Exclusions
                        excluded = False
                        for ex in rules["exclusions"]:
                            if ex.lower() in name_lower:
                                excluded = True
                                p_copy = dict(p_unique)
                                p_copy["status"] = "excluded"
                                p_copy["reason"] = f"matched exclusion keyword: {ex}"
                                excluded_products.append(p_copy)
                                break
                                
                        if excluded:
                            continue
                            
                        # Keywords
                        has_keyword = False
                        for kw in rules["keywords"]:
                            if kw.lower() in name_lower:
                                has_keyword = True
                                break
                                
                        if not has_keyword:
                            p_copy = dict(p_unique)
                            p_copy["status"] = "excluded"
                            p_copy["reason"] = "did not match required commodity keywords"
                            excluded_products.append(p_copy)
                            continue
                            
                        # Classification
                        variants = classify_variants(name, rules["variant_keywords"])
                        
                        # Normalization
                        qty_str = p_unique.get("quantity", "")
                        quantity_kg = normalize_quantity(qty_str)
                        
                        # Price per kg
                        price_per_kg = None
                        try:
                            price_val = float(p_unique.get("price"))
                            if quantity_kg and quantity_kg > 0:
                                price_per_kg = round(price_val / quantity_kg, 2)
                        except (ValueError, TypeError):
                            pass
                            
                        valid_products.append({
                            "name": name,
                            "commodity": commodity_id,
                            "variant": variants,
                            "quantity": qty_str,
                            "quantity_kg": quantity_kg,
                            "price": float(p_unique["price"]) if p_unique.get("price") is not None else None,
                            "mrp": float(p_unique["mrp"]) if p_unique.get("mrp") is not None else None,
                            "price_per_kg": price_per_kg
                        })
                        
                    # Save Excluded
                    excluded_path = CLEAN_DIR / f"zepto_{commodity_id}_excluded.json"
                    with open(excluded_path, "w", encoding="utf-8") as f:
                        json.dump({"excluded_products": excluded_products}, f, indent=2, ensure_ascii=False)
                        
                    # Save Clean
                    clean_output = {
                        "platform": "zepto",
                        "commodity": commodity_id,
                        "location": LOCATION,
                        "collected_at": datetime.now().isoformat(),
                        "summary": {
                            "raw_count": len(extracted_products),
                            "unique_count": len(unique_products),
                            "valid_count": len(valid_products),
                            "excluded_count": len(excluded_products)
                        },
                        "products": valid_products
                    }
                    clean_path = CLEAN_DIR / f"zepto_{commodity_id}_clean.json"
                    with open(clean_path, "w", encoding="utf-8") as f:
                        json.dump(clean_output, f, indent=2, ensure_ascii=False)
                        
                    # Record Summary
                    run_summaries[commodity_id] = {
                        "status": "SUCCESS",
                        "raw_count": len(extracted_products),
                        "unique_count": len(unique_products),
                        "valid_count": len(valid_products),
                        "excluded_count": len(excluded_products)
                    }
                    print(f"  -> Found {len(valid_products)} valid products.\n")
                    
                except Exception as e:
                    print(f"  -> [FAILED] Error extracting {commodity_id}: {e}\n")
                    run_summaries[commodity_id] = {
                        "status": "FAILED",
                        "error": str(e)
                    }
                    
        except Exception as e:
            print(f"\n[FATAL ERROR] An error occurred setting up: {e}")
            screenshot_path = BASE_DIR / "zepto_error_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            
        finally:
            print("Closing browser...")
            browser.close()
            
        # Print Final Summary
        print("\n========================================")
        print("ZEPTO MULTI-COMMODITY COLLECTION")
        print("========================================")
        print(f"Location: {LOCATION}\n")
        
        success_count = 0
        total_valid = 0
        total_excluded = 0
        
        for comm, summary in run_summaries.items():
            print(f"{comm.capitalize()}")
            if summary["status"] == "SUCCESS":
                success_count += 1
                total_valid += summary["valid_count"]
                total_excluded += summary["excluded_count"]
                print(f"  Raw: {summary['raw_count']}")
                print(f"  Unique: {summary['unique_count']}")
                print(f"  Valid: {summary['valid_count']}")
                print(f"  Excluded: {summary['excluded_count']}")
                print(f"  Status: SUCCESS\n")
            else:
                print(f"  Status: FAILED ({summary.get('error')})\n")
                
        print("========================================")
        print(f"TOTAL SUCCESSFUL COMMODITIES: {success_count}/{len(COMMODITY_RULES)}")
        print(f"TOTAL VALID PRODUCTS: {total_valid}")
        print(f"TOTAL EXCLUDED PRODUCTS: {total_excluded}")
        print("========================================\n")


if __name__ == "__main__":
    run()