import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_player(page, url):
    print(f"Scraping {url}...")
    await page.goto(url)
    # await page.wait_for_load_state('networkidle') # Sometimes too strict, maybe just wait for content

    player_data = {"url": url}

    # 1. Player Name
    try:
        # Try to find the name in the header or table
        name_elem = await page.query_selector("h1")
        if name_elem:
            player_data["player_name"] = await name_elem.inner_text()
    except Exception as e:
        print(f"Error extracting name: {e}")

    # 2. Details (Team, Country, Birthday, Name, Bio, Game)
    try:
        details = {}
        # Look for common labels
        labels = ["Team", "Country", "Name", "Birthday"]
        for label in labels:
            # XPath to find a cell with the label, then the next cell or sibling
            element = await page.query_selector(f"xpath=//td[contains(text(), '{label}')]/following-sibling::td")
            if not element:
                 element = await page.query_selector(f"xpath=//div[contains(text(), '{label}')]/following-sibling::div")
            
            if element:
                text = await element.inner_text()
                details[label.lower()] = text.strip()
        
        # Extract bio text (the description paragraph)
        try:
            bio_elem = await page.query_selector("xpath=//p[contains(@class, 'bio') or contains(., 'was born on') or contains(., 'is currently playing')]")
            if not bio_elem:
                # Try to find any paragraph that has player info
                bio_elem = await page.query_selector("xpath=//div[contains(@class, 'player')]//p")
            if bio_elem:
                details["bio"] = await bio_elem.inner_text()
        except:
            pass
        
        # Extract game information
        try:
            # Look for game tags like "CS2 Settings", "Valorant Settings", etc.
            game_elem = await page.query_selector("xpath=//h2[contains(text(), 'Settings')] | //h3[contains(text(), 'Settings')]")
            if game_elem:
                game_text = await game_elem.inner_text()
                # Extract game name from text like "CS2 Settings" -> "CS2"
                game_name = game_text.replace("Settings", "").strip()
                details["game"] = game_name
            
            # Alternative: check for game tags/badges
            if "game" not in details:
                game_badge = await page.query_selector("xpath=//a[contains(@href, '/games/')] | //span[contains(@class, 'game')]")
                if game_badge:
                    details["game"] = await game_badge.inner_text()
        except:
            pass
            
        player_data["details"] = details
    except Exception as e:
        print(f"Error extracting details: {e}")

    # 3. Mouse Settings
    try:
        mouse_settings = {}
        # Look for the Mouse section
        # Assuming a table under a "Mouse" header
        # We can look for specific keys like DPI, Sensitivity, etc.
        mouse_keys = ["DPI", "Sensitivity", "eDPI", "Zoom Sensitivity", "Hz", "Windows Sensitivity"]
        for key in mouse_keys:
             # Try to find the key and the value below or next to it
             # Often these are in a grid: Label -> Value
             # Let's try to find the text and get the value
             # Using a generic approach: find text, get parent, find value
             # Or specific selectors if we knew them.
             # Based on image, it looks like:
             # DPI
             # 400
             # So maybe a div with text DPI, and a sibling or child.
             
             # Let's try to find the element containing the key, then get the text of the next element or a specific class
             # A robust way is to look for the text, then look at the next element in the DOM flow
             
             # Attempt 1: Table cell approach (if it's a table)
             # Attempt 2: Div block approach
             
             # Let's try a specific selector for the values if possible, but generic is better.
             # Let's try to grab all text under the "Mouse" section if possible.
             pass
        
        # Alternative: Select the container for Mouse settings and parse text
        # Let's try to find a table or grid that contains "DPI"
        dpi_elem = await page.query_selector("xpath=//*[text()='DPI']/following::*[1]") # Very generic
        if dpi_elem:
             # This might be too generic.
             pass

        # Let's use a more targeted approach for the Mouse section
        # Find the header "Mouse"
        # Then find the container below it
        
        # For now, let's try to grab the whole mouse section text to see structure if we fail
        # But let's try to implement specific extraction
        
        # Re-examining the image:
        # DPI       Sensitivity
        # 400       3.09
        # This looks like a grid.
        
        # Let's try to find elements with class that might indicate value.
        # Or just iterate over known keys.
        for key in mouse_keys:
             # XPath: Find element with text 'key', then get the element immediately following it in the DOM (or a child)
             # Assuming they are close.
             # //div[contains(text(), 'DPI')]/following-sibling::div
             val = await page.evaluate(f"""(key) => {{
                const labels = Array.from(document.querySelectorAll('div, td, th, span, p'));
                const label = labels.find(el => el.textContent.trim() === key);
                if (label) {{
                    // Try next sibling
                    let next = label.nextElementSibling;
                    if (next) return next.textContent.trim();
                    // Try parent's next sibling (if label is wrapped)
                    if (label.parentElement && label.parentElement.nextElementSibling) {{
                        return label.parentElement.nextElementSibling.textContent.trim();
                    }}
                }}
                return null;
             }}""", key)
             if val:
                 mouse_settings[key] = val
        player_data["mouse_settings"] = mouse_settings

    except Exception as e:
        print(f"Error extracting mouse settings: {e}")

    # 4. Gear
    try:
        gear = []
        # Look for the "Gear" section
        # Items usually have an image and a name.
        # Let's look for the "Gear" header and then the items following it.
        # Or look for specific categories: Monitor, Mouse, Keyboard, Headset, etc.
        categories = ["Monitor", "Mouse", "Keyboard", "Headset", "Mousepad", "Earphones"]
        
        # We can look for these category tags (often small badges) and the associated product name.
        for cat in categories:
             # Find element with text 'cat' (case insensitive maybe?)
             # Then find the product name associated with it.
             # Often: [Badge: Monitor] [Image] [Name: ZOWIE XL2546]
             
             product = await page.evaluate(f"""(cat) => {{
                const badges = Array.from(document.querySelectorAll('div, span, p'));
                const badge = badges.find(el => el.textContent.trim() === cat);
                if (badge) {{
                    let current = badge.parentElement;
                    let card = null;
                    
                    // Traverse up but check for other categories to avoid grabbing the whole list
                    const allCats = {json.dumps(categories)};
                    
                    while (current && current.tagName !== 'BODY') {{
                        // Check if this container has other categories (excluding the current one)
                        // This is expensive but safer.
                        // Actually, just check if it has multiple badges.
                        // A simple heuristic: A card shouldn't be too large.
                        if (current.innerText.length > 500) break; // Reduced limit
                        
                        // Check if we found a likely card container (e.g. has class 'card' or is an 'a' tag)
                        if (current.tagName === 'A' || current.className.includes('card') || current.className.includes('item')) {{
                            card = current;
                            break;
                        }}
                        current = current.parentElement;
                    }}
                    
                    if (!card) card = badge.parentElement; // Fallback to immediate parent
                    
                    if (card) {{
                        const clone = card.cloneNode(true);
                        // Remove the badge
                        const cloneBadge = Array.from(clone.querySelectorAll('*')).find(el => el.textContent.trim() === cat);
                        if (cloneBadge) cloneBadge.remove();
                        
                        // Clean up text: take the first non-empty line
                        const text = clone.innerText.trim();
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        // The product name is usually the first line, but sometimes "Check price" or "More from" is there.
                        // Filter out common noise
                        const cleanLines = lines.filter(l => !l.includes('Check price') && !l.includes('More from'));
                        return cleanLines.length > 0 ? cleanLines[0] : text;
                    }}
                }}
                return null;
             }}""", cat)
             
             if product:
                 gear.append({"category": cat, "name": product})
        
        player_data["gear"] = gear

    except Exception as e:
        print(f"Error extracting gear: {e}")
        
    # 5. Setup & Streaming
    try:
        setup = []
        categories = ["Chair", "Microphone", "Webcam"]
        for cat in categories:
             product = await page.evaluate(f"""(cat) => {{
                const badges = Array.from(document.querySelectorAll('div, span, p'));
                const badge = badges.find(el => el.textContent.trim() === cat);
                if (badge) {{
                    let current = badge.parentElement;
                    let card = null;
                    const allCats = {json.dumps(categories)};
                    
                    while (current && current.tagName !== 'BODY') {{
                        if (current.innerText.length > 500) break;
                        if (current.tagName === 'A' || current.className.includes('card') || current.className.includes('item')) {{
                            card = current;
                            break;
                        }}
                        current = current.parentElement;
                    }}
                    
                    if (!card) card = badge.parentElement;
                    
                    if (card) {{
                        const clone = card.cloneNode(true);
                        const cloneBadge = Array.from(clone.querySelectorAll('*')).find(el => el.textContent.trim() === cat);
                        if (cloneBadge) cloneBadge.remove();
                        
                        const text = clone.innerText.trim();
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        const cleanLines = lines.filter(l => !l.includes('Check price') && !l.includes('More from'));
                        return cleanLines.length > 0 ? cleanLines[0] : text;
                    }}
                }}
                return null;
             }}""", cat)
             if product:
                 setup.append({"category": cat, "name": product})
        player_data["setup"] = setup

    except Exception as e:
        print(f"Error extracting setup: {e}")

    return player_data

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        all_data = []
        page_num = 1
        
        while True:
            if page_num == 1:
                url = "https://prosettings.net/players/"
            else:
                url = f"https://prosettings.net/players/page/{page_num}/"
            
            print(f"Navigating to {url}...")
            try:
                response = await page.goto(url)
                if response.status == 404:
                    print("Page not found. Stopping.")
                    break
            except Exception as e:
                print(f"Error loading page {url}: {e}")
                break
            
            # Extract links
            links = await page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href^="https://prosettings.net/players/"]'));
                return anchors.map(a => a.href).filter((v, i, a) => a.indexOf(v) === i);
            }""")
            
            if not links:
                 links = await page.evaluate("""() => {
                    const anchors = Array.from(document.querySelectorAll('a[href^="/players/"]'));
                    return anchors.map(a => "https://prosettings.net" + a.getAttribute("href")).filter((v, i, a) => a.indexOf(v) === i);
                }""")
            
            # Filter out pagination links if any (though regex above should handle it mostly, but /players/page/X/ matches /players/)
            # The regex `^https://prosettings.net/players/` matches `.../players/page/2/` too.
            # We need to exclude /page/ links.
            links = [l for l in links if "/page/" not in l and l != "https://prosettings.net/players/"]
            
            if not links:
                print(f"No player links found on page {page_num}. Stopping.")
                break
                
            print(f"Found {len(links)} player links on page {page_num}.")
            
            for link in links:
                # Check if we already scraped this (duplicates across pages?)
                if any(d['url'] == link for d in all_data):
                    continue
                    
                data = await scrape_player(page, link)
                all_data.append(data)
                
            # Save incrementally
            with open('prosettings_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
            
            page_num += 1
            # Optional: Limit for testing if needed, but user asked for ALL.
            # if page_num > 3: break 
        
        print(f"Done. Scraped {len(all_data)} players. Saved to prosettings_data.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
