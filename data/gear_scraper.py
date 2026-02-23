import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_gear_details(page, url):
    """Scrape detailed information from a gear review page"""
    print(f"Scraping gear details from {url}...")
    
    try:
        await page.goto(url, timeout=30000)
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return None
    
    gear_data = {"url": url}
    
    # Extract gear name from title
    try:
        title_elem = await page.query_selector("h1")
        if title_elem:
            gear_data["name"] = await title_elem.inner_text()
    except:
        pass
    
    # Extract Pros
    try:
        pros = []
        # Look for the Pros section
        pros_section = await page.query_selector("xpath=//h2[contains(text(), 'Pros')] | //h3[contains(text(), 'Pros')]")
        if pros_section:
            # Get the list items following the Pros heading
            pros_items = await page.evaluate("""() => {
                const prosHeading = Array.from(document.querySelectorAll('h2, h3')).find(h => h.textContent.includes('Pros'));
                if (!prosHeading) return [];
                
                const items = [];
                let next = prosHeading.nextElementSibling;
                while (next && next.tagName !== 'H2' && next.tagName !== 'H3') {
                    if (next.tagName === 'UL' || next.tagName === 'OL') {
                        const listItems = Array.from(next.querySelectorAll('li'));
                        items.push(...listItems.map(li => li.textContent.trim()));
                        break;
                    }
                    next = next.nextElementSibling;
                }
                return items;
            }""")
            pros = pros_items
        gear_data["pros"] = pros
    except Exception as e:
        print(f"Error extracting pros: {e}")
        gear_data["pros"] = []
    
    # Extract Cons
    try:
        cons = []
        cons_items = await page.evaluate("""() => {
            const consHeading = Array.from(document.querySelectorAll('h2, h3')).find(h => h.textContent.includes('Cons'));
            if (!consHeading) return [];
            
            const items = [];
            let next = consHeading.nextElementSibling;
            while (next && next.tagName !== 'H2' && next.tagName !== 'H3') {
                if (next.tagName === 'UL' || next.tagName === 'OL') {
                    const listItems = Array.from(next.querySelectorAll('li'));
                    items.push(...listItems.map(li => li.textContent.trim()));
                    break;
                }
                next = next.nextElementSibling;
            }
            return items;
        }""")
        cons = cons_items
        gear_data["cons"] = cons
    except Exception as e:
        print(f"Error extracting cons: {e}")
        gear_data["cons"] = []
    
    # Extract Specs
    try:
        specs = {}
        specs_data = await page.evaluate("""() => {
            const specsHeading = Array.from(document.querySelectorAll('h2, h3')).find(h => h.textContent.includes('Specs'));
            if (!specsHeading) return {};
            
            const specsObj = {};
            let next = specsHeading.nextElementSibling;
            
            // Look for a table or list of specs
            while (next && next.tagName !== 'H2' && next.tagName !== 'H3') {
                if (next.tagName === 'TABLE') {
                    const rows = Array.from(next.querySelectorAll('tr'));
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td, th');
                        if (cells.length >= 2) {
                            const key = cells[0].textContent.trim();
                            const value = cells[1].textContent.trim();
                            if (key) specsObj[key] = value;
                        }
                    });
                    break;
                }
                // Also handle div-based layouts
                const labels = next.querySelectorAll('[class*="label"], [class*="spec-name"]');
                const values = next.querySelectorAll('[class*="value"], [class*="spec-value"]');
                if (labels.length > 0 && values.length > 0) {
                    for (let i = 0; i < Math.min(labels.length, values.length); i++) {
                        const key = labels[i].textContent.trim();
                        const value = values[i].textContent.trim();
                        if (key) specsObj[key] = value;
                    }
                }
                next = next.nextElementSibling;
            }
            return specsObj;
        }""")
        specs = specs_data
        gear_data["specs"] = specs
    except Exception as e:
        print(f"Error extracting specs: {e}")
        gear_data["specs"] = {}
    
    return gear_data

async def main():
    # Load existing player data to extract gear URLs
    try:
        with open('prosettings_data.json', 'r', encoding='utf-8') as f:
            players_data = json.load(f)
    except FileNotFoundError:
        print("Error: prosettings_data.json not found. Please run the player scraper first.")
        return
    
    # Extract all unique gear items and their potential URLs
    gear_items = {}
    for player in players_data:
        gear_list = player.get("gear", [])
        for gear in gear_list:
            gear_name = gear.get("name", "")
            if gear_name and gear_name not in gear_items:
                # Create a potential review URL from gear name
                # Convert to lowercase, replace spaces with hyphens
                url_slug = gear_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
                potential_url = f"https://prosettings.net/reviews/{url_slug}/"
                gear_items[gear_name] = {
                    "name": gear_name,
                    "category": gear.get("category", ""),
                    "review_url": potential_url
                }
    
    print(f"Found {len(gear_items)} unique gear items to scrape.")
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        all_gear_data = []
        
        for gear_name, gear_info in list(gear_items.items())[:100]:  # Limit for testing
            url = gear_info["review_url"]
            gear_data = await scrape_gear_details(page, url)
            
            if gear_data:
                gear_data["category"] = gear_info["category"]
                all_gear_data.append(gear_data)
                
                # Save incrementally
                with open('gear_data.json', 'w', encoding='utf-8') as f:
                    json.dump(all_gear_data, f, indent=4, ensure_ascii=False)
            
            # Small delay
            await asyncio.sleep(0.5)
        
        print(f"Done. Scraped {len(all_gear_data)} gear items. Saved to gear_data.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
