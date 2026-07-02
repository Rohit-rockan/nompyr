import re
from bs4 import BeautifulSoup
import cloudscraper

BASE_URL = "https://animotvslash.org"

def get_scraper():
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

def scrape_home_animotvslash():
    scraper = get_scraper()
    
    sections = {"latest_updates": []}
    
    try:
        req = scraper.get(BASE_URL)
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            
            # Find widgets or latest updates
            # Often .bixbox is used in this theme
            bixboxes = soup.select('.bixbox')
            
            for box in bixboxes:
                title_elem = box.select_one('.releases h3, .releases h2')
                section_title = title_elem.text.strip() if title_elem else "Recent"
                
                items = box.select('article.bs')
                if not items:
                    continue
                    
                parsed_items = []
                for item in items:
                    a_tag = item.select_one('a')
                    if not a_tag:
                        continue
                        
                    href = a_tag.get('href', '')
                    if not href.startswith(BASE_URL):
                        continue
                        
                    title = a_tag.get('title')
                    if not title:
                        title_tt = item.select_one('.tt')
                        title = title_tt.text.strip() if title_tt else "Unknown"
                        
                    img_tag = item.select_one('img')
                    image = img_tag.get('src') if img_tag else None
                    if image and image.startswith('//'):
                        image = "https:" + image
                        
                    # Extract ID from URL (e.g. /anime/naruto-x-ut/ or /episode-1/)
                    slug = href.rstrip('/').split('/')[-1]
                    url = f"/anime/animotvslash/{slug}"
                    
                    parsed_items.append({
                        "id": slug,
                        "title": title,
                        "image": image,
                        "url": url,
                        "type": "TV"
                    })
                    
                if parsed_items:
                    sections["latest_updates"].extend(parsed_items)
    except Exception as e:
        return {"error": str(e)}, 500
    return sections

def search_animotvslash(query):
    scraper = get_scraper()
    
    try:
        req = scraper.get(f"{BASE_URL}/?s={query}")
        if req.status_code != 200:
            return []
            
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.select('article.bs')
        
        results = []
        for item in items:
            a_tag = item.select_one('a')
            if not a_tag:
                continue
                
            href = a_tag.get('href', '')
            title = a_tag.get('title')
            if not title:
                title_tt = item.select_one('.tt')
                title = title_tt.text.strip() if title_tt else "Unknown"
                
            img_tag = item.select_one('img')
            image = img_tag.get('src') if img_tag else None
            if image and image.startswith('//'):
                image = "https:" + image
                
            slug = href.rstrip('/').split('/')[-1]
            # Since WP search can return posts/episodes instead of anime, check if it's anime
            if '/anime/' not in href:
                # we just skip or treat it as anime, but typically better to skip
                pass 
                
            url = f"/anime/animotvslash/{slug}"
            
            results.append({
                "id": slug,
                "title": title,
                "image": image,
                "url": url,
                "type": "TV"
            })
            
        return results
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_animotvslash(anime_id):
    scraper = get_scraper()
    
    info_url = f"{BASE_URL}/anime/{anime_id}/"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return None
        
    soup = BeautifulSoup(req.text, 'html.parser')
    
    title_elem = soup.select_one('.infox h1')
    title = title_elem.text.strip() if title_elem else anime_id
    
    img_elem = soup.select_one('.thumb img')
    image = img_elem.get('src') if img_elem else None
    
    desc_elem = soup.select_one('.entry-content')
    description = desc_elem.text.strip() if desc_elem else ""
    
    info = {
        "id": anime_id,
        "title": title,
        "image": image,
        "description": description,
        "episodes": []
    }
    
    episodes = soup.select('.eplister li')
    for ep in episodes:
        a_tag = ep.select_one('a')
        if not a_tag:
            continue
            
        ep_href = a_tag.get('href', '')
        ep_slug = ep_href.rstrip('/').split('/')[-1]
        
        num_elem = ep.select_one('.epl-num')
        num = num_elem.text.strip() if num_elem else "1"
        
        title_e = ep.select_one('.epl-title')
        ep_title = title_e.text.strip() if title_e else f"Episode {num}"
        
        info["episodes"].append({
            "id": ep_slug,
            "number": num,
            "title": ep_title
        })
        
    info["totalEpisodes"] = len(info["episodes"])
    # Theme episode lists are usually descending, reverse them to ascending
    info["episodes"].reverse()
        
    return info

def fetch_servers_animotvslash(episode_id):
    scraper = get_scraper()
    
    # URL is base_url/episode_id/
    url = f"{BASE_URL}/{episode_id}/"
    try:
        req = scraper.get(url)
        if req.status_code != 200:
            return []
            
        soup = BeautifulSoup(req.text, 'html.parser')
        iframe = soup.select_one('iframe')
        
        servers = []
        if iframe and iframe.get('src'):
            servers.append({
                "name": "HD Server (Animotvslash)",
                "url": iframe.get('src'),
                "type": "iframe"
            })
            
        return servers
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_source_animotvslash(server_url):
    return server_url
