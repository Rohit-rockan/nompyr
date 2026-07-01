import cloudscraper
from bs4 import BeautifulSoup
from core.config import Config
import re
import urllib.parse
from scrapers.base import get_headers

BASE_URL = "https://anidb.app"

def get_scraper():
    return cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def scrape_home_anidb():
    url = f"{BASE_URL}/home"
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.REQUEST_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        home_data = {
            "top_trending": {"NOW": []},
            "latest_updates": [],
            "popular": []
        }
        
        # In anidb.app, home page has multiple sections
        # Example parsing trending (we'll look for sections with swiper containers)
        # Note: anidb's home is heavily styled. We'll pick cards with class "anime-card"
        # We can just return a generic list for now as 'latest'
        sections = soup.select('section')
        for idx, section in enumerate(sections):
            cards = section.select('.anime-card')
            section_list = []
            for card in cards:
                href = card.get('href') or ''
                if not href.startswith('http'):
                    href = BASE_URL + href
                
                title_elem = card.select_one('p.font-semibold') or card.select_one('p')
                title = title_elem.text.strip() if title_elem else "Unknown"
                
                img_elem = card.select_one('img')
                image = img_elem.get('src') if img_elem else None
                
                # Extract ID
                m = re.search(r'/anime/([^/]+)', href)
                anime_id = m.group(1) if m else None
                
                if not anime_id:
                    continue
                    
                section_list.append({
                    "id": anime_id,
                    "title": title,
                    "image": image,
                    "url": href
                })
            
            if idx == 0:
                home_data['top_trending']["NOW"] = section_list
            elif idx == 1:
                home_data['latest_updates'] = section_list
            elif idx == 2:
                home_data['popular'] = section_list
        
        if not home_data['latest_updates'] and home_data['top_trending']["NOW"]:
            home_data['latest_updates'] = home_data['top_trending']["NOW"]
            
        return home_data
    except Exception as e:
        print(f"Error scraping anidb home: {e}")
        return {"trending": [], "latest": [], "top": []}

def search_anidb(query):
    url = f"{BASE_URL}/browse?q={urllib.parse.quote(query)}"
    results = []
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.REQUEST_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        cards = soup.select('.anime-card')
        for card in cards:
            href = card.get('href') or ''
            if not href.startswith('http'):
                href = BASE_URL + href
                
            title_elem = card.select_one('p.font-semibold') or card.select_one('p')
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            img_elem = card.select_one('img')
            image = img_elem.get('src') if img_elem else None
            
            m = re.search(r'/anime/([^/]+)', href)
            anime_id = m.group(1) if m else None
            
            if anime_id:
                results.append({
                    "id": anime_id,
                    "title": title,
                    "image": image,
                    "url": href
                })
    except Exception as e:
        print(f"Error searching anidb: {e}")
    return results

def scrape_anime_info_anidb(anime_id):
    url = f"{BASE_URL}/anime/{anime_id}"
    info = {
        "id": anime_id,
        "title": "Unknown",
        "image": None,
        "description": "",
        "episodes": []
    }
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.REQUEST_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        title_elem = soup.select_one('h1')
        if title_elem:
            info['title'] = title_elem.text.strip()
            
        img_elem = soup.select_one('img.object-cover')
        if img_elem:
            info['image'] = img_elem.get('src')
            
        desc_elem = soup.select_one('div.text-muted') # approximate description block
        if desc_elem:
            info['description'] = desc_elem.text.strip()
            
        # To get episodes, we need the numeric ID
        # anime_id usually looks like "naruto-3686"
        numeric_id_match = re.search(r'-(\d+)$', anime_id)
        if numeric_id_match:
            num_id = numeric_id_match.group(1)
            eps_url = f"{BASE_URL}/api/frontend/anime/{num_id}/episodes"
            eps_r = scraper.get(eps_url, timeout=Config.REQUEST_TIMEOUT)
            if eps_r.status_code == 200:
                eps_data = eps_r.json()
                for ep in eps_data.get('episodes', []):
                    info['episodes'].append({
                        "id": str(ep['id']),
                        "number": ep.get('number', 0),
                        "title": f"Episode {ep.get('number', 0)}",
                        "is_filler": ep.get('filler', False)
                    })
                    
    except Exception as e:
        print(f"Error scraping anidb info: {e}")
    return info

def fetch_servers_anidb(anime_id, episode_id):
    servers = []
    try:
        scraper = get_scraper()
        # Episode languages API gives us the embed URLs directly
        lang_url = f"{BASE_URL}/api/frontend/episode/{episode_id}/languages"
        r = scraper.get(lang_url, timeout=Config.REQUEST_TIMEOUT)
        if r.status_code == 200:
            lang_data = r.json()
            for lang in lang_data.get('languages', []):
                embed_url = lang.get('embed_url')
                if embed_url:
                    servers.append({
                        "name": f"AniDB ({lang.get('name', 'Sub')})",
                        "type": "embed",
                        "url": embed_url,
                        "server_id": embed_url
                    })
    except Exception as e:
        print(f"Error fetching servers for anidb: {e}")
    return servers

def resolve_source_anidb(server_id):
    # Server_id is the embed URL
    try:
        scraper = get_scraper()
        r = scraper.get(server_id, timeout=Config.REQUEST_TIMEOUT)
        if r.status_code == 200:
            # Look for the .m3u8 file in the script block
            m3u8_match = re.search(r'file:\s*[\'\"]([^\'\"]+\.m3u8[^\'\"]*)[\'\"]', r.text)
            if m3u8_match:
                stream_url = m3u8_match.group(1)
                return {
                    "sources": [{"url": stream_url, "type": "hls"}],
                    "subtitles": []
                }
    except Exception as e:
        print(f"Error resolving source for anidb: {e}")
    return None
