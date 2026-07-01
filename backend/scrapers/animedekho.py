import re
from bs4 import BeautifulSoup
import cloudscraper

BASE_URL = "https://animedekho.app"

def get_scraper():
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

def scrape_home_animedekho():
    scraper = get_scraper()
    sections = {"latest_updates": []}
    
    try:
        # animedekho home content is actually at /home/
        req = scraper.get(f"{BASE_URL}/home/")
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            
            # Since the home page is just a list of articles, we'll put them in one section
            articles = soup.select('article.post')
            
            parsed_items = []
            for item in articles:
                title_elem = item.select_one('.entry-title')
                title = title_elem.text.strip() if title_elem else "Unknown"
                
                a_tag = item.select_one('a.btn.lin') or item.select_one('a')
                if not a_tag:
                    continue
                    
                href = a_tag.get('href', '')
                if not href.startswith(BASE_URL):
                    continue
                    
                slug = href.rstrip('/').split('/')[-1]
                
                # Check if it's movie or series
                media_type = "Movie" if "/movie" in href else "TV"
                
                url = f"/anime/animedekho/{slug}"
                
                # Try to find image
                bg_div = item.select_one('.bg')
                image = None
                if bg_div and bg_div.get('style'):
                    m = re.search(r'url\((.*?)\)', bg_div.get('style'))
                    if m:
                        image = m.group(1).strip("'\"")
                        
                parsed_items.append({
                    "id": slug,
                    "title": title,
                    "image": image,
                    "url": url,
                    "type": media_type
                })
                
            if parsed_items:
                sections["latest_updates"].extend(parsed_items)
    except Exception as e:
        print(f"Error fetching animedekho home: {e}")
        
    return sections

def search_animedekho(query):
    scraper = get_scraper()
    try:
        req = scraper.get(f"{BASE_URL}/?s={query}")
        if req.status_code != 200:
            return []
            
        soup = BeautifulSoup(req.text, 'html.parser')
        articles = soup.select('article.post')
        
        results = []
        for item in articles:
            title_elem = item.select_one('.entry-title')
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            a_tag = item.select_one('a.btn.lin') or item.select_one('a')
            if not a_tag:
                continue
                
            href = a_tag.get('href', '')
            slug = href.rstrip('/').split('/')[-1]
            media_type = "Movie" if "/movie" in href else "TV"
            url = f"/anime/animedekho/{slug}"
            
            bg_div = item.select_one('.bg')
            image = None
            if bg_div and bg_div.get('style'):
                m = re.search(r'url\((.*?)\)', bg_div.get('style'))
                if m:
                    image = m.group(1).strip("'\"")
                    
            results.append({
                "id": slug,
                "title": title,
                "image": image,
                "url": url,
                "type": media_type
            })
            
        return results
    except Exception as e:
        print(f"animedekho search error: {e}")
        return []

def scrape_anime_info_animedekho(anime_id):
    scraper = get_scraper()
    
    # Try series first, then movie
    urls_to_try = [
        f"{BASE_URL}/series-hindi/{anime_id}/",
        f"{BASE_URL}/movie-hindi/{anime_id}/",
        f"{BASE_URL}/series/{anime_id}/",
        f"{BASE_URL}/movie/{anime_id}/"
    ]
    
    soup = None
    final_url = ""
    for url in urls_to_try:
        req = scraper.get(url)
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            final_url = url
            break
            
    if not soup:
        return None
        
    title_elem = soup.select_one('.entry-title')
    title = title_elem.text.strip() if title_elem else anime_id
    
    img_elem = soup.select_one('figure img')
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
    
    # If movie, it's just one episode
    if "/movie" in final_url:
        info["episodes"].append({
            "id": anime_id,
            "number": 1,
            "title": title
        })
    else:
        # Find episodes
        episodes_blocks = soup.select('div > div:has(h3.title) + div a.btn.sm')
        for ep_btn in episodes_blocks:
            ep_href = ep_btn.get('href', '')
            ep_slug = ep_href.rstrip('/').split('/')[-1]
            
            parent = ep_btn.parent.parent
            title_e = parent.select_one('h3.title')
            ep_title = title_e.text.strip() if title_e else ep_slug
            
            # Extract number
            num = ep_slug
            m = re.search(r'-(\d+)x(\d+)$', ep_slug)
            if m:
                num = m.group(2)
                
            info["episodes"].append({
                "id": ep_slug,
                "number": num,
                "title": ep_title
            })
            
    info["totalEpisodes"] = len(info["episodes"])
    
    return info

def fetch_servers_animedekho(episode_id):
    scraper = get_scraper()
    
    # URL is base_url/epi/episode_id/ or base_url/movie-hindi/episode_id/
    url = f"{BASE_URL}/epi/{episode_id}/"
    req = scraper.get(url)
    
    if req.status_code != 200:
        # Try movie
        url = f"{BASE_URL}/movie-hindi/{episode_id}/"
        req = scraper.get(url)
        if req.status_code != 200:
            return []
            
    soup = BeautifulSoup(req.text, 'html.parser')
    iframes = soup.select('iframe')
    
    servers = []
    for i, iframe in enumerate(iframes):
        src = iframe.get('src')
        if src:
            servers.append({
                "name": f"Server {i+1} (Animedekho)",
                "url": src,
                "type": "iframe"
            })
            
    return servers

def resolve_source_animedekho(server_url):
    return server_url
