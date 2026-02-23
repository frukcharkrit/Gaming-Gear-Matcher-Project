import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import aiohttp

# Category mappings
CATEGORIES = {
    "mice": {
        "json_file": "mice_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Mouse"
    },
    "keyboards": {
        "json_file": "keyboards_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Keyboard"
    },
    "monitors": {
        "json_file": "monitors_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Monitor"
    },
    "headsets": {
        "json_file": "headsets_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Headset"
    },
    "mousepads": {
        "json_file": "mousepads_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Mousepad"
    },
    "chairs": {
        "json_file": "chairs_reviews_data.json",
        "folder": r"D:\data\Gaming Gear Pictures\Chair"
    }
}

def sanitize_filename(name):
    """Sanitize filename by removing invalid characters"""
    # Remove 'Review' suffix if present
    name = re.sub(r'\s+Review\s*$', '', name, flags=re.IGNORECASE)
    # Replace invalid characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace multiple spaces/underscores with single underscore
    name = re.sub(r'[\s_]+', '_', name)
    # Remove leading/trailing underscores
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
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

async def get_review_image(page, review_url):
    """Get the main image URL from a review page"""
    try:
        await page.goto(review_url, timeout=30000)
        await page.wait_for_load_state('domcontentloaded', timeout=30000)
        
        # Try to find the main review image
        # Common selectors for featured/main images
        image_url = await page.evaluate("""() => {
            // Try featured image first
            let img = document.querySelector('.wp-post-image');
            if (img && img.src) return img.src;
            
            // Try article image
            img = document.querySelector('article img');
            if (img && img.src) return img.src;
            
            // Try first content image
            img = document.querySelector('.entry-content img, .post-content img');
            if (img && img.src) return img.src;
            
            // Try any image in main content
            img = document.querySelector('main img, .content img');
            if (img && img.src) return img.src;
            
            return null;
        }""")
        
        return image_url
    except Exception as e:
        print(f"Error getting image from {review_url}: {e}")
        return None

async def main():
    # Create HTTP session for downloading
    async with aiohttp.ClientSession() as session:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            print("="*60)
            print("GEAR REVIEW IMAGE DOWNLOADER")
            print("="*60)
            
            total_downloaded = 0
            
            for category, info in CATEGORIES.items():
                json_file = info["json_file"]
                output_folder = info["folder"]
                
                # Create folder if it doesn't exist
                os.makedirs(output_folder, exist_ok=True)
                
                # Load review data
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        reviews = json.load(f)
                except FileNotFoundError:
                    print(f"\n{category.upper()}: Skipping (no data file)")
                    continue
                
                if len(reviews) == 0:
                    print(f"\n{category.upper()}: Skipping (no reviews)")
                    continue
                
                print(f"\n{'='*60}")
                print(f"{category.upper()}: Downloading {len(reviews)} images")
                print(f"Folder: {output_folder}")
                print(f"{'='*60}")
                
                downloaded = 0
                
                for i, review in enumerate(reviews, 1):
                    name = review.get('name', '')
                    url = review.get('url', '')
                    
                    if not name or not url:
                        continue
                    
                    # Sanitize filename
                    filename = sanitize_filename(name)
                    
                    print(f"[{i}/{len(reviews)}] {filename[:50]}... ", end="", flush=True)
                    
                    # Check if already downloaded
                    existing_files = [
                        os.path.join(output_folder, f"{filename}.jpg"),
                        os.path.join(output_folder, f"{filename}.png"),
                        os.path.join(output_folder, f"{filename}.webp"),
                        os.path.join(output_folder, f"{filename}.jpeg")
                    ]
                    
                    if any(os.path.exists(f) for f in existing_files):
                        print("⏭️ (exists)")
                        downloaded += 1
                        continue
                    
                    # Get image URL from review page
                    image_url = await get_review_image(page, url)
                    
                    if not image_url:
                        print("✗ (no image)")
                        continue
                    
                    # Determine file extension
                    ext = '.jpg'
                    if '.png' in image_url.lower():
                        ext = '.png'
                    elif '.webp' in image_url.lower():
                        ext = '.webp'
                    elif '.jpeg' in image_url.lower():
                        ext = '.jpeg'
                    
                    filepath = os.path.join(output_folder, f"{filename}{ext}")
                    
                    # Download image
                    success = await download_image(session, image_url, filepath)
                    
                    if success:
                        print("✓")
                        downloaded += 1
                    else:
                        print("✗ (download failed)")
                    
                    await asyncio.sleep(0.2)
                
                print(f"\n✓ Downloaded {downloaded}/{len(reviews)} images for {category.upper()}")
                total_downloaded += downloaded
            
            await browser.close()
            
            # Final summary
            print("\n" + "="*60)
            print("DOWNLOAD COMPLETE")
            print("="*60)
            print(f"Total images downloaded: {total_downloaded}")
            
            for category, info in CATEGORIES.items():
                folder = info["folder"]
                if os.path.exists(folder):
                    count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
                    print(f"{category.upper()}: {count} images in {folder}")

if __name__ == "__main__":
    asyncio.run(main())
