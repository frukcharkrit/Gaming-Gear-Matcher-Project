import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import aiohttp

CATEGORIES = {
    "mice": {  
        "url": "https://prosettings.net/gear/lists/mice/",
        "folder": r"D:\data\Gaming Gear Pictures\Mouse",
        "expected": 360
    },
    "keyboards": {
        "url": "https://prosettings.net/gear/lists/keyboards/",
        "folder": r"D:\data\Gaming Gear Pictures\Keyboard",
        "expected": 253
    },
    "monitors": {
        "url": "https://prosettings.net/gear/lists/monitors/",
        "folder": r"D:\data\Gaming Gear Pictures\Monitor",
        "expected": 103
    },
    "headsets": {
        "url": "https://prosettings.net/gear/lists/headsets/",
        "folder": r"D:\data\Gaming Gear Pictures\Headset",
        "expected": 159
    },
    "mousepads": {
        "url": "https://prosettings.net/gear/lists/mousepads/",
        "folder": r"D:\data\Gaming Gear Pictures\Mousepad",
        "expected": 287
    },
    "chairs": {
        "url": "https://prosettings.net/gear/lists/chairs/",
        "folder": r"D:\data\Gaming Gear Pictures\Chair",
        "expected": 35
    }
}

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\s_]+', '_', name)
    return name.strip('_')

async def download_image(session, url, filepath):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                with open(filepath, 'wb') as f:
                    f.write(await response.read())
                return True
    except:
        pass
    return False

async def scrape_all_gear(page, category_url, category_name, expected_count):
    """Scrape ALL gear from category - FIXED SELECTOR"""
    print(f"\n{'='*60}")
    print(f"Scraping {category_name} (expecting ~{expected_count} items)")
    print(f"{'='*60}")
    
    all_gear = []
    page_num = 1
    
    while True:
        url = f"{category_url}page/{page_num}/" if page_num > 1 else category_url
        
        try:
            print(f"  Loading page {page_num}...", end=" ", flush=True)
            await page.goto(url, wait_until='domcontentloaded', timeout=120000)
            await asyncio.sleep(3)  # Wait for table to load
            print("✓")
        except Exception as e:
            print(f"✗")
            if page_num == 1:
                return []
            break
        
        # FIXED: Image is in 2nd td, not 1st
        gear_items = await page.evaluate("""() => {
            const items = [];
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                // Second cell contains the product link and image
                const secondCell = row.querySelector('td:nth-child(2)');
                if (!secondCell) return;
                
                const link = secondCell.querySelector('a');
                if (!link) return;
                
                const name = link.textContent.trim();
                const img = link.querySelector('img');
                
                if (name && img && img.src) {
                    items.push({
                        name: name,
                        image_url: img.src
                    });
                }
            });
            
            return items;
        }""")
        
        if len(gear_items) == 0:
            print(f"  No items found on page {page_num}")
            break
        
        # Add unique items
        new_items = 0
        for item in gear_items:
            if not any(g['name'] == item['name'] for g in all_gear):
                all_gear.append(item)
                new_items += 1
        
        print(f"  Page {page_num}: {len(gear_items)} items, {new_items} new (Total: {len(all_gear)})")
        
        # Check progress
        if len(all_gear) >= expected_count:
            print(f"  ✓ Reached expected count")
            break
        
        page_num += 1
        await asyncio.sleep(1)
        
        if page_num > 100:
            break
    
    print(f"\n✓ Scraped {len(all_gear)} items")
    return all_gear

async def main():
    async with aiohttp.ClientSession() as session:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            print("="*60)
            print("COMPLETE GEAR LIST IMAGE DOWNLOADER")
            print("Expected total: 1,197 images")
            print("="*60)
            
            grand_total = 0
            
            for category, info in CATEGORIES.items():
                os.makedirs(info["folder"], exist_ok=True)
                
                # Scrape items
                items = await scrape_all_gear(page, info["url"], category.upper(), info["expected"])
                
                if not items:
                    print(f"⚠️ No items for {category}\n")
                    continue
                
                # Download
                print(f"\nDownloading {len(items)} {category} images...")
                print("-"*60)
                
                downloaded = 0
                skipped = 0
                
                for i, item in enumerate(items, 1):
                    fname = sanitize_filename(item['name'])
                    
                    # Progress indicator
                    if i % 20 == 0 or i == len(items):
                        print(f"[{i}/{len(items)}] {fname[:30]}... ", end="", flush=True)
                    else:
                        if i % 5 == 0:
                            print(f"{i} ", end="", flush=True)
                    
                    # Check existing
                    existing = [
                        os.path.join(info["folder"], f"{fname}.{ext}")
                        for ext in ['jpg', 'png', 'webp', 'jpeg']
                    ]
                    
                    if any(os.path.exists(f) for f in existing):
                        if i % 20 == 0:
                            print("⏭️")
                        skipped += 1
                        continue
                    
                    # Download
                    ext = '.png' if '.png' in item['image_url'].lower() else '.jpg'
                    filepath = os.path.join(info["folder"], f"{fname}{ext}")
                    
                    if await download_image(session, item['image_url'], filepath):
                        if i % 20 == 0:
                            print("✓")
                        downloaded += 1
                    else:
                        if i % 20 == 0:
                            print("✗")
                    
                    await asyncio.sleep(0.03)
                
                total_in_folder = downloaded + skipped
                print(f"\n\n✓ {category.upper()}: {total_in_folder}/{info['expected']} images")
                print(f"  New: {downloaded}, Skipped: {skipped}")
                
                grand_total += total_in_folder
            
            await browser.close()
            
            # Summary
            print("\n" + "="*60)
            print("COMPLETE!")
            print("="*60)
            
            for category, info in CATEGORIES.items():
                if os.path.exists(info["folder"]):
                    count = len([f for f in os.listdir(info["folder"]) 
                                if os.path.isfile(os.path.join(info["folder"], f))])
                    print(f"{category.upper()}: {count}/{info['expected']} images")
            
            print(f"\nTOTAL: {grand_total}/1197 images")
            print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
