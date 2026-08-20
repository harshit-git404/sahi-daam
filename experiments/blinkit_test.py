import json
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from commodity_rules import COMMODITY_RULES, normalize_quantity, classify_variants

LOCATION = "Katpadi, Vellore" # Example target location
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
CLEAN_DIR = OUTPUT_DIR / "clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print("========================================")
    print("BLINKIT SCRAPER PROOF OF CONCEPT")
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
            print("Navigating to Blinkit...")
            page.goto("https://blinkit.com/")
            
            print(f"\n[!] ACTION REQUIRED IN BROWSER [!]")
            print(f"Blinkit usually prompts for a delivery location.")
            print(f"Please manually set the location to: {LOCATION}")
            print("Waiting up to 60 seconds for the main search bar to become enabled...")
            
            # Wait for the search bar to appear and be clickable
            page.wait_for_selector("input[placeholder*='Search']", timeout=60000, state="visible")
            print("\nLocation seems set. Starting multi-commodity extraction...\n")
            
            for commodity_id, rules in COMMODITY_RULES.items():
                search_term = rules["search_term"]
                print(f"--- Processing {commodity_id.upper()} ---")
                
                try:
                    # Navigate directly to the search page for the commodity
                    page.goto(f"https://blinkit.com/s/?q={search_term}")
                    
                    # Wait for results to load
                    time.sleep(5)
                    
                    product_cards = page.locator("a[data-test-id='plp-product']").all()
                    if not product_cards:
                        product_cards = page.locator("div").filter(has_text="ADD").all()

                    extracted_products = []
                    for card in product_cards:
                        try:
                            text = card.inner_text().strip()
                            if not text:
                                continue
                            
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            
                            product = {
                                "name": "Unknown",
                                "quantity": "Unknown",
                                "price": None,
                                "mrp": None,
                                "raw_text": lines
                            }
                            
                            # Simple line heuristic
                            for line in lines:
                                cleaned_line = line.replace("â‚¹", "₹").replace("Ã¢â€šÂ¹", "₹").strip()
                                lower_line = cleaned_line.lower()
                                if any(kw in lower_line for kw in rules["keywords"]) and len(cleaned_line) < 60:
                                    product["name"] = cleaned_line
                                elif any(q in lower_line for q in [" g", " kg", " pc", " pcs", " bunch", " pack"]):
                                    product["quantity"] = cleaned_line
                                elif "₹" in cleaned_line or "â‚¹" in line:
                                    price_numbers = re.findall(r"\d+(?:\.\d+)?", cleaned_line)
                                    if price_numbers:
                                        val = price_numbers[0]
                                        if product["price"] is None:
                                            product["price"] = float(val)
                                        elif product["mrp"] is None:
                                            product["mrp"] = float(val)
                            
                            extracted_products.append(product)
                        except Exception:
                            pass
                            
                    # Save raw output
                    raw_output = {
                        "platform": "blinkit",
                        "commodity_search": search_term,
                        "location": LOCATION,
                        "collected_at": datetime.now().isoformat(),
                        "products": extracted_products
                    }
                    raw_path = RAW_DIR / f"blinkit_{commodity_id}_raw.json"
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
                                p_unique["status"] = "excluded"
                                p_unique["reason"] = f"matched exclusion keyword: {ex}"
                                excluded_products.append(p_unique)
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
                            p_unique["status"] = "excluded"
                            p_unique["reason"] = "did not match required commodity keywords"
                            excluded_products.append(p_unique)
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
                            "price": float(p_unique["price"]) if p_unique.get("price") else None,
                            "mrp": float(p_unique["mrp"]) if p_unique.get("mrp") else None,
                            "price_per_kg": price_per_kg
                        })
                        
                    # Save Excluded
                    excluded_path = CLEAN_DIR / f"blinkit_{commodity_id}_excluded.json"
                    with open(excluded_path, "w", encoding="utf-8") as f:
                        json.dump({"excluded_products": excluded_products}, f, indent=2, ensure_ascii=False)
                        
                    # Save Clean
                    clean_output = {
                        "platform": "blinkit",
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
                    clean_path = CLEAN_DIR / f"blinkit_{commodity_id}_clean.json"
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
            screenshot_path = BASE_DIR / "error_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            
        finally:
            print("Closing browser...")
            browser.close()
            
        # Print Final Summary
        print("\n========================================")
        print("BLINKIT MULTI-COMMODITY COLLECTION")
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

