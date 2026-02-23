import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import aiohttp

async def download_image(session, url, filepath):
    """Download an image from URL to filepath"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                with open(filepath, 'wb') as f:
                    f.write(await response.read())
                return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

async def scrape_player_image(page, url, session, output_dir):
    """Scrape player image from their profile page"""
    print(f"Scraping image from {url}...")
    try:
        await page.goto(url, timeout=30000)
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return None

    player_data = {"url": url}

    # 1. Player Name
    try:
        name_elem = await page.query_selector("h1")
        if name_elem:
            player_data["player_name"] = await name_elem.inner_text()
    except Exception as e:
        print(f"Error extracting name: {e}")
        return None

    # 2. Player Image
    try:
        # The player profile image has class 'wp-post-image' and alt attribute matching player name
        img_elem = await page.query_selector("img.wp-post-image")
        
        if not img_elem:
            # Fallback: try to find image with alt matching player name
            player_name = player_data.get("player_name", "")
            if player_name:
                img_elem = await page.query_selector(f"img[alt='{player_name}']")
        
        if img_elem:
            img_url = await img_elem.get_attribute("src")
            if img_url:
                # Make URL absolute if relative
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://prosettings.net" + img_url
                
                player_data["image_url"] = img_url
                
                # Clean player name for filename
                player_name = player_data.get("player_name", "unknown")
                # Remove special characters and spaces
                safe_name = re.sub(r'[<>:"/\\|?*]', '', player_name)
                safe_name = safe_name.strip()
                
                # Get file extension from URL
                ext = os.path.splitext(img_url)[1]
                if not ext or len(ext) > 5:
                    ext = ".jpg"
                
                filename = f"{safe_name}{ext}"
                filepath = os.path.join(output_dir, filename)
                
                # Download the image
                downloaded = await download_image(session, img_url, filepath)
                if downloaded:
                    player_data["image_path"] = filepath
                    print(f"✓ Downloaded: {filename}")
                else:
                    print(f"✗ Failed to download: {filename}")
    except Exception as e:
        print(f"Error extracting image: {e}")

    return player_data

async def main():
    output_dir = r"D:\data\Pictures"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        # Create aiohttp session for downloading images
        async with aiohttp.ClientSession() as session:
            all_data = []
            page_num = 1
            
            while True:
                if page_num == 1:
                    url = "https://prosettings.net/players/"
                else:
                    url = f"https://prosettings.net/players/page/{page_num}/"
                
                print(f"\nNavigating to {url}...")
                try:
                    response = await page.goto(url)
                    if response.status == 404:
                        print("Page not found. Stopping.")
                        break
                except Exception as e:
                    print(f"Error loading page {url}: {e}")
                    break
                
                # Extract player profile links
                links = await page.evaluate("""() => {
                    const anchors = Array.from(document.querySelectorAll('a[href^="https://prosettings.net/players/"]'));
                    return anchors.map(a => a.href).filter((v, i, a) => a.indexOf(v) === i);
                }""")
                
                if not links:
                    links = await page.evaluate("""() => {
                        const anchors = Array.from(document.querySelectorAll('a[href^="/players/"]'));
                        return anchors.map(a => "https://prosettings.net" + a.getAttribute("href")).filter((v, i, a) => a.indexOf(v) === i);
                    }""")
                
                # Filter out pagination and main players page links
                links = [l for l in links if "/page/" not in l and l != "https://prosettings.net/players/"]
                
                if not links:
                    print(f"No player links found on page {page_num}. Stopping.")
                    break
                
                print(f"Found {len(links)} player links on page {page_num}.")
                
                for link in links:
                    # Check if we already scraped this
                    if any(d.get('url') == link for d in all_data):
                        continue
                    
                    data = await scrape_player_image(page, link, session, output_dir)
                    if data:
                        all_data.append(data)
                    
                    # Small delay to be polite
                    await asyncio.sleep(0.5)
                
                # Save progress incrementally
                with open('player_images_data.json', 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=4, ensure_ascii=False)
                
                page_num += 1
                
                # Optional: Uncomment to limit pages for testing
                # if page_num > 3: break
            
            print(f"\n✓ Done! Downloaded images for {len(all_data)} players.")
            print(f"Images saved to: {output_dir}")
            print(f"Metadata saved to: player_images_data.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
