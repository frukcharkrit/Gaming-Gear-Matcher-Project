import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import aiohttp

CATEGORIES = {
    "mice": {
        "url": "https://prosettings.net/gear/lists/mice/",
        "folder": r"D:\data\Gaming Gear Pictures\Mouse"
    },
    "keyboards": {
        "url": "https://prosettings.net/gear/lists/keyboards/",
        "folder": r"D:\data\Gaming Gear Pictures\Keyboard"
    },
    "monitors": {
        "url": "https://prosettings.net/gear/lists/monitors/",
        "folder": r"D:\data\Gaming Gear Pictures\Monitor"
    },
    "headsets": {
        "url": "https://prosettings.net/gear/lists/headsets/",
        "folder": r"D:\data\Gaming Gear Pictures\Headset"
    },
    "mousepads": {
        "url": "https://prosettings.net/gear/lists/mousepads/",
        "folder": r"D:\data\Gaming Gear Pictures\Mousepad"
    },
    "chairs": {
        "url": "https://prosettings.net/gear/lists/chairs/",
        "folder": r"D:\data\Gaming Gear Pictures\Chair"
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

async def scrape_gear_images(page, category_url, category_name):
    print(f"\nScraping {category_name} images...")
    
    all_gear = []
    page_num = 1
    
    while page_num <= 50:
        url = f"{category_url}page/{page_num}/" if page_num > 1 else category_url
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=120000)
            await asyncio.sleep(3)
        except:
            if page_num > 1:
                break
            print(f"  Skipping {category_name} - page load error")
            return []
        
        gear_items = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('tbody tr').forEach(row => {
                const cell = row.querySelector('td:first-child');
                if (!cell) return;
                const link = cell.querySelector('a');
                if (!link) return;
                const img = link.querySelector('img');
                if (img && img.src) {
                    items.push({ name: link.textContent.trim(), image_url: img.src });
                }
            });
            return items;
        }""")
        
        if not gear_items:
            break
        
        for item in gear_items:
            if not any(g['name'] == item['name'] for g in all_gear):
                all_gear.append(item)
        
        print(f"  Page {page_num}: +{len(gear_items)} items (Total: {len(all_gear)})")
        page_num += 1
        await asyncio.sleep(1)
    
    return all_gear

async def main():
    async with aiohttp.ClientSession() as session:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            print("=" * 60)
            print("GEAR LIST IMAGE DOWNLOADER")
            print("=" * 60)
            
            total = 0
            
            for category, info in CATEGORIES.items():
                os.makedirs(info["folder"], exist_ok=True)
                
                print(f"\n{'=' * 60}")
                print(f"{category.upper()}: Scraping gear list")
                print(f"{'=' * 60}")
                
                items = await scrape_gear_images(page, info["url"], category.upper())
                
                if not items:
                    continue
                
                print(f"\n{category.upper()}: Downloading {len(items)} images")
                
                downloaded = 0
                for i, item in enumerate(items, 1):
                    fname = sanitize_filename(item['name'])
                    print(f"[{i}/{len(items)}] {fname[:35]}... ", end="", flush=True)
                    
                    existing = [os.path.join(info["folder"], f"{fname}.{ext}") for ext in ['jpg', 'png', 'webp', 'jpeg']]
                    if any(os.path.exists(f) for f in existing):
                        print("⏭️")
                        downloaded += 1
                        continue
                    
                    ext = '.webp' if '.webp' in item['image_url'].lower() else ('.png' if '.png' in item['image_url'].lower() else '.jpg')
                    path = os.path.join(info["folder"], f"{fname}{ext}")
                    
                    if await download_image(session, item['image_url'], path):
                        print("✓")
                        downloaded += 1
                    else:
                        print("✗")
                    
                    await asyncio.sleep(0.05)
                
                print(f"\n✓ {downloaded}/{len(items)} for {category.upper()}")
                total += downloaded
            
            await browser.close()
            
            print("\n" + "=" * 60)
            print("COMPLETE")
            print("=" * 60)
            print(f"Total new downloads: {total}")
            
            for category, info in CATEGORIES.items():
                if os.path.exists(info["folder"]):
                    count = len([f for f in os.listdir(info["folder"]) if os.path.isfile(os.path.join(info["folder"], f))])
                    print(f"{category.upper()}: {count} total images")

if __name__ == "__main__":
    asyncio.run(main())

