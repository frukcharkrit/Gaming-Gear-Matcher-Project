import asyncio
import json
from playwright.async_api import async_playwright

# Category mappings with their URLs and output files
CATEGORIES = {
    "mice": {
        "url": "https://prosettings.net/gear/lists/mice/",
        "output_file": "mice_data.json"
    },
    "keyboards": {
        "url": "https://prosettings.net/gear/lists/keyboards/",
        "output_file": "keyboards_data.json"
    },
    "monitors": {
        "url": "https://prosettings.net/gear/lists/monitors/",
        "output_file": "monitors_data.json"
    },
    "headsets": {
        "url": "https://prosettings.net/gear/lists/headsets/",
        "output_file": "headsets_data.json"
    },
    "mousepads": {
        "url": "https://prosettings.net/gear/lists/mousepads/",
        "output_file": "mousepads_data.json"
    },
    "chairs": {
        "url": "https://prosettings.net/gear/lists/chairs/",
        "output_file": "chairs_data.json"
    }
}

async def scrape_gear_table(page, url, category_name):
    """Scrape gear data from a category table"""
    print(f"\nScraping {category_name} from {url}...")
    
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=60000)
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return []
    
    # Extract table data using JavaScript
    gear_data = await page.evaluate("""() => {
        const table = document.querySelector('table');
        if (!table) return [];
        
        const data = [];
        const headers = [];
        
        // Get headers
        const headerRow = table.querySelector('thead tr');
        if (headerRow) {
            const headerCells = headerRow.querySelectorAll('th');
            headerCells.forEach(th => {
                const headerText = th.textContent.trim();
                // Skip Usage and Reviews columns
                if (headerText && !headerText.includes('Usage') && !headerText.includes('Review')) {
                    headers.push(headerText);
                }
            });
        }
        
        // Get rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const item = {};
            const cells = row.querySelectorAll('td');
            
            let headerIndex = 0;
            cells.forEach((cell, cellIndex) => {
                // Get the corresponding header from thead
                const allHeaders = table.querySelectorAll('thead tr th');
                if (cellIndex < allHeaders.length) {
                    const headerText = allHeaders[cellIndex].textContent.trim();
                    
                    // Skip Usage and Reviews columns
                    if (headerText.includes('Usage') || headerText.includes('Review')) {
                        return;
                    }
                    
                    // Extract text content, handle links
                    let value = cell.textContent.trim();
                    
                    // For name column, try to get the link text
                    if (headerText === 'Name' || cellIndex === 0) {
                        const link = cell.querySelector('a');
                        if (link) {
                            value = link.textContent.trim();
                        }
                    }
                    
                    if (headerText) {
                        item[headerText] = value;
                    }
                }
            });
            
            if (Object.keys(item).length > 0) {
                data.push(item);
            }
        });
        
        return data;
    }""")
    
    print(f"Extracted {len(gear_data)} items from {category_name}")
    return gear_data

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        for category, info in CATEGORIES.items():
            url = info["url"]
            output_file = info["output_file"]
            
            # Scrape the category
            data = await scrape_gear_table(page, url, category)
            
            # Save to file
            if data:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"✓ Saved {len(data)} items to {output_file}")
            else:
                print(f"✗ No data found for {category}")
            
            # Small delay between categories
            await asyncio.sleep(1)
        
        await browser.close()
        print("\n✓ Done! All gear data saved to category-specific JSON files.")

if __name__ == "__main__":
    asyncio.run(main())
