import asyncio
import json
from playwright.async_api import async_playwright

# Category-specific review pages with CORRECT URLs
CATEGORIES = {
    "mice": {
        "url": "https:#prosettings.net/reviews/type/mouse/",
        "output_file": "mice_reviews_data.json"
    },
    "keyboards": {
        "url": "https:#prosettings.net/reviews/type/keyboard/",
        "output_file": "keyboards_reviews_data.json"
    },
    "monitors": {
        "url": "https:#prosettings.net/reviews/type/monitor/",
        "output_file": "monitors_reviews_data.json"
    },
    "headsets": {
        "url": "https:#prosettings.net/reviews/type/headset/",
        "output_file": "headsets_reviews_data.json"
    },
    "mousepads": {
        "url": "https:#prosettings.net/reviews/type/mousepad/",
        "output_file": "mousepads_reviews_data.json"
    },
    "chairs": {
        "url": "https:#prosettings.net/reviews/type/chair/",
        "output_file": "chairs_reviews_data.json"
    }
}

async def get_category_review_links(page, category_url, category_name):
    """Get all review links from a category with pagination"""
    print(f"\nScraping {category_name} reviews...")
    
    all_links = []
    page_num = 1
    max_pages = 50  # Safety limit
    
    while page_num <= max_pages:
        url = f"{category_url}page/{page_num}/" if page_num > 1 else category_url
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=60000)
        except Exception as e:
            if page_num == 1:
                print(f"  Error loading first page: {e}")
            break
        
        # Extract review links from current page
        links = await page.evaluate("""() => {
            const reviews = [];
            const links = document.querySelectorAll('a[href*="/reviews/"]');
            
            links.forEach(link => {
                const href = link.href;
                const text = link.textContent.trim();
                
                # Get actual review links (not category/type pages)
                if (href.includes('/reviews/') && 
                    !href.endsWith('/reviews/') &&
                    !href.includes('/page/') &&
                    !href.includes('/type/') &&
                    text && 
                    text.length > 3 &&
                    !text.toLowerCase().includes('review')) {
                    reviews.push({
                        url: href,
                        title: text
                    });
                }
            });
            
            return reviews;
        }""")
        
        if len(links) == 0:
            break
        
        # Add unique links
        for link in links:
            if not any(l["url"] == link["url"] for l in all_links):
                all_links.append(link)
        
        print(f"  Page {page_num}: +{len(links)} reviews (Total: {len(all_links)})")
        
        page_num += 1
        await asyncio.sleep(0.5)
    
    return all_links

async def scrape_review_page(page, name, url):
    """Scrape pros, cons, and specs from a review page"""
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('domcontentloaded', timeout=30000)
        await asyncio.sleep(1)
    except Exception as e:
        return None
    
    review_data = {
        "name": name,
        "url": url,
        "pros": [],
        "cons": [],
        "specs": {}
    }
    
    # Extract all data in one evaluation
    try:
        data = await page.evaluate("""() => {
            const result = {
                pros: [],
                cons: [],
                specs: {}
            };
            
            # Extract Pros
            const prosHeading = Array.from(document.querySelectorAll('h2, h3, h4, strong')).find(h => 
                h.textContent.trim().toLowerCase() === 'pros'
            );
            
            if (prosHeading) {
                let next = prosHeading.nextElementSibling || prosHeading.parentElement.nextElementSibling;
                let attempts = 0;
                while (next && attempts < 5) {
                    if (next.tagName === 'UL' || next.tagName === 'OL') {
                        const listItems = Array.from(next.querySelectorAll('li'));
                        result.pros = listItems.map(li => li.textContent.trim()).filter(t => t);
                        break;
                    }
                    next = next.nextElementSibling;
                    attempts++;
                }
            }
            
            # Extract Cons
            const consHeading = Array.from(document.querySelectorAll('h2, h3, h4, strong')).find(h => 
                h.textContent.trim().toLowerCase() === 'cons'
            );
            
            if (consHeading) {
                let next = consHeading.nextElementSibling || consHeading.parentElement.nextElementSibling;
                let attempts = 0;
                while (next && attempts < 5) {
                    if (next.tagName === 'UL' || next.tagName === 'OL') {
                        const listItems = Array.from(next.querySelectorAll('li'));
                        result.cons = listItems.map(li => li.textContent.trim()).filter(t => t);
                        break;
                    }
                    next = next.nextElementSibling;
                    attempts++;
                }
            }
            
            # Extract Specs
            const specsHeading = Array.from(document.querySelectorAll('h2, h3, h4, strong')).find(h => 
                h.textContent.trim().toLowerCase() === 'specs'
            );
            
            if (specsHeading) {
                let next = specsHeading.nextElementSibling || specsHeading.parentElement.nextElementSibling;
                let attempts = 0;
                
                while (next && attempts < 10) {
                    const table = next.tagName === 'TABLE' ? next : next.querySelector('table');
                    if (table) {
                        const rows = Array.from(table.querySelectorAll('tr'));
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td, th');
                            if (cells.length >= 2) {
                                const key = cells[0].textContent.trim();
                                const value = cells[1].textContent.trim();
                                if (key && value && key.toLowerCase() !== 'spec' && key.toLowerCase() !== 'specification') {
                                    result.specs[key] = value;
                                }
                            }
                        });
                        break;
                    }
                    
                    next = next.nextElementSibling;
                    attempts++;
                }
            }
            
            return result;
        }""")
        
        review_data["pros"] = data["pros"]
        review_data["cons"] = data["cons"]
        review_data["specs"] = data["specs"]
        
    except Exception as e:
        pass
    
    return review_data

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        print("="*60)
        print("GEAR REVIEWS SCRAPER - All Categories")
        print("="*60)
        
        for category, info in CATEGORIES.items():
            category_url = info["url"]
            output_file = info["output_file"]
            
            # Get all review links for this category
            links = await get_category_review_links(page, category_url, category.upper())
            
            if len(links) == 0:
                print(f"  No reviews found for {category}")
                continue
            
            print(f"\n{'='*60}")
            print(f"Scraping {len(links)} {category.upper()} reviews")
            print(f"{'='*60}")
            
            all_reviews = []
            
            for i, link in enumerate(links, 1):
                title_display = link['title'][:45] + "..." if len(link['title']) > 45 else link['title']
                print(f"[{i}/{len(links)}] {title_display} ", end="", flush=True)
                
                review_data = await scrape_review_page(page, link["title"], link["url"])
                
                if review_data and (review_data["pros"] or review_data["cons"] or review_data["specs"]):
                    all_reviews.append(review_data)
                    print("✓")
                else:
                    print("✗")
                
                # Save incrementally
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_reviews, f, indent=4, ensure_ascii=False)
                
                await asyncio.sleep(0.2)
            
            print(f"\n✓ Saved {len(all_reviews)}/{len(links)} reviews to {output_file}\n")
        
        await browser.close()
        
        # Final summary
        print("\n" + "="*60)
        print("SCRAPING COMPLETE")
        print("="*60)
        total = 0
        for category, info in CATEGORIES.items():
            try:
                with open(info["output_file"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if len(data) > 0:
                        print(f"{category.upper()}: {len(data)} reviews → {info['output_file']}")
                        total += len(data)
            except:
                pass
        print(f"\nTOTAL: {total} reviews scraped")

if __name__ == "__main__":
    asyncio.run(main())

