import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import aiohttp

# Category mappings for gear lists
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
    """Sanitize filename by removing invalid characters"""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\s_]+', '_', name)
    name = name.strip('_')
    return name

async def download_image(session, url, filepath):
    """Download image from URL and save to filepath"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content = await response.read()
                with open(filepath, 'wb') as f:
                    f.write(content)
                return True
    except:
        pass
    return False

async def scrape_gear_images(page, category_url, category_name):
    """Scrape gear images from category list page with pagination"""
    print(f"\nScraping {category_name} images...")
    
    all_gear = []
    page_num = 1
    max_pages = 50
    
    while page_num <= max_pages:
        url = f"{category_url}page/{page_num}/" if page_num > 1 else category_url
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=90000)
            await asyncio.sleep(2)
        except Exception as e:
            if page_num == 1:
                print(f"  Error: {str(e)[:100]}")
            break
        
        # Extract gear data
        gear_items = await page.evaluate("""() => {
            const items = [];
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const firstCell = row.querySelector('td:first-child');
                if (!firstCell) return;
                
                const nameLink = firstCell.querySelector('a');
                if (!nameLink) return;
                
                const name = nameLink.textContent.trim();
                const img = nameLink.querySelector('img');
                const imageUrl = img ? img.src : null;
                
                if (name && imageUrl) {
                    items.push({ name: name, image_url: imageUrl });
                }
            });
            
            return items;
        }""")
        
        if len(gear_items) == 0:
            break
        
        for item in gear_items:
            if not any(g['name'] == item['name'] for g in all_gear):
                all_gear.append(item)
        
        print(f"  Page {page_num}: +{len(gear_items)} items (Total: {len(all_gear)})")
        page_num += 1
        await asyncio.sleep(0.5)
    
    return all_gear

async def main():
    async with aiohttp.ClientSession() as session:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print("="*60)
            print("GEAR LIST IMAGE DOWNLOADER - ALL GEAR")
            print("="*60)
            
            total_downloaded = 0
            
            for category, info in CATEGORIES.items():
                category_url = info["url"]
                output_folder = info["folder"]
                
                os.makedirs(output_folder, exist_ok=True)
                
                print(f"\n{'='*60}")
                print(f"{category.upper()}: Scraping gear list")
                print(f"{'='*60}")
                
                gear_items = await scrape_gear_images(page, category_url, category.upper())
                
                if len(gear_items) == 0:
                    print(f"No items found for {category}")
                    continue
                
                print(f"\n{'='*60}")
                print(f"{category.upper()}: Downloading {len(gear_items)} images")
                print(f"{'='*60}")
                
                downloaded = 0
                
                for i, item in enumerate(gear_items, 1):
                    name = item['name']
                    image_url = item['image_url']
                    filename = sanitize_filename(name)
                    
                    print(f"[{i}/{len(gear_items)}] {filename[:40]}... ", end="", flush=True)
                    
                    # Check if exists
                    existing = [
                        os.path.join(output_folder, f"{filename}.jpg"),
                        os.path.join(output_folder, f"{filename}.png"),
                        os.path.join(output_folder, f"{filename}.webp"),
                        os.path.join(output_folder, f"{filename}.jpeg")
                    ]
                    
                    if any(os.path.exists(f) for f in existing):
                        print("⏭️")
                        downloaded += 1
                        continue
                    
                    # Determine extension
                    ext = '.jpg'
                    if '.png' in image_url.lower():
                        ext = '.png'
                    elif '.webp' in image_url.lower():
                        ext = '.webp'
                    elif '.jpeg' in image_url.lower():
                        ext = '.jpeg'
                    
                    filepath = os.path.join(output_folder, f"{filename}{ext}")
                    
                    if await download_image(session, image_url, filepath):
                        print("✓")
                        downloaded += 1
                    else:
                        print("✗")
                    
                    await asyncio.sleep(0.05)
                
                print(f"\n✓ Downloaded {downloaded}/{len(gear_items)} images for {category.upper()}")
                total_downloaded += downloaded
            
            await browser.close()
            
            print("\n" + "="*60)
            print("DOWNLOAD COMPLETE")
            print("="*60)
            print(f"Total new images downloaded: {total_downloaded}")
            
            for category, info in CATEGORIES.items():
                folder = info["folder"]
                if os.path.exists(folder):
                    count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
                    print(f"{category.upper()}: {count} total images in {folder}")

if __name__ == "__main__":
    asyncio.run(main())
