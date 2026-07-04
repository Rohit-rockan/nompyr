import cloudscraper
from bs4 import BeautifulSoup
from config import Config
import re
import urllib.parse

BASE_URL = "https://anidb.app"

def get_scraper():
    return cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def scrape_home_anidb():
    url = f"{BASE_URL}/home"
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        home_data = {
            "banner": [],
            "latest_updates": [],
            "top_trending": {
                "NOW": [],
                "DAY": [],
                "WEEK": [],
                "MONTH": []
            },
            "popular": [],
            "upcoming": []
        }
        
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
                image = img_elem.get('src') if img_elem else ""
                
                m = re.search(r'/anime/([^/]+)', href)
                anime_id = m.group(1) if m else ""
                
                if not anime_id:
                    continue
                    
                section_list.append({
                    "title": title,
                    "japanese_title": "",
                    "poster": image,
                    "url": href,
                    "slug": anime_id,
                    "current_episode": "",
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "type": "TV"
                })
            
            if idx == 0:
                home_data['top_trending']["NOW"] = section_list
                home_data['top_trending']["DAY"] = section_list
                home_data['top_trending']["WEEK"] = section_list
                home_data['top_trending']["MONTH"] = section_list
            elif idx == 1:
                home_data['latest_updates'] = section_list
            elif idx == 2:
                home_data['popular'] = section_list
        
        if not home_data['latest_updates'] and home_data['top_trending']["NOW"]:
            home_data['latest_updates'] = home_data['top_trending']["NOW"]
            
        return home_data
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_anidb(keyword, page=1):
    url = f"{BASE_URL}/browse?q={urllib.parse.quote(keyword)}"
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        cards = soup.select('.anime-card')
        results = []
        for card in cards:
            href = card.get('href') or ''
            if not href.startswith('http'):
                href = BASE_URL + href
                
            title_elem = card.select_one('p.font-semibold') or card.select_one('p')
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            img_elem = card.select_one('img')
            image = img_elem.get('src') if img_elem else ""
            
            m = re.search(r'/anime/([^/]+)', href)
            anime_id = m.group(1) if m else ""
            
            if anime_id:
                results.append({
                    "title": title,
                    "japanese_title": "",
                    "slug": anime_id,
                    "url": href,
                    "poster": image,
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "total_episodes": "",
                    "year": "",
                    "type": "TV",
                    "rating": "",
                    "genres": []
                })
                
        return {
            "total": len(results),
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_anidb(slug):
    url = f"{BASE_URL}/anime/{slug}"
    try:
        scraper = get_scraper()
        r = scraper.get(url, timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        title_elem = soup.select_one('h1')
        title = title_elem.text.strip() if title_elem else "Unknown"
            
        img_elem = soup.select_one('img.object-cover')
        image = img_elem.get('src') if img_elem else ""
            
        desc_elem = soup.select_one('div.text-muted') # approximate description block
        description = desc_elem.text.strip() if desc_elem else ""
            
        return {
            "ani_id": slug,
            "title": title,
            "japanese_title": "",
            "description": description,
            "poster": image,
            "banner": image,
            "sub_episodes": "",
            "dub_episodes": "",
            "type": "TV",
            "rating": "",
            "mal_score": "",
            "detail": {
                "studio": "",
                "released": "",
                "views": "",
                "likes": "",
                "dislikes": "",
                "downloads": "",
                "genres": []
            },
            "seasons": []
        }
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes_anidb(slug):
    try:
        scraper = get_scraper()
        numeric_id_match = re.search(r'-(\d+)$', slug)
        if not numeric_id_match:
            return []
            
        num_id = numeric_id_match.group(1)
        eps_url = f"{BASE_URL}/api/frontend/anime/{num_id}/episodes"
        eps_r = scraper.get(eps_url, timeout=Config.SCRAPER_TIMEOUT)
        
        episodes = []
        if eps_r.status_code == 200:
            eps_data = eps_r.json()
            for ep in eps_data.get('episodes', []):
                ep_id = str(ep['id'])
                episodes.append({
                    "number": str(ep.get('number', 0)),
                    "slug": ep_id,
                    "title": f"Episode {ep.get('number', 0)}",
                    "japanese_title": "",
                    "token": f"anidb:{slug}:{ep_id}",
                    "has_sub": True,
                    "has_dub": False
                })
        return episodes
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_servers_anidb(ep_token):
    try:
        if not ep_token.startswith("anidb:"):
            return {"error": "Invalid episode token"}, 400
            
        parts = ep_token.split(":")
        episode_id = parts[2]
        
        servers = []
        scraper = get_scraper()
        lang_url = f"{BASE_URL}/api/frontend/episode/{episode_id}/languages"
        r = scraper.get(lang_url, timeout=Config.SCRAPER_TIMEOUT)
        if r.status_code == 200:
            lang_data = r.json()
            for lang in lang_data.get('languages', []):
                embed_url = lang.get('embed_url')
                if embed_url:
                    servers.append({
                        "name": f"AniDB ({lang.get('name', 'Sub')})",
                        "server_id": embed_url,
                        "episode_id": episode_id,
                        "link_id": f"anidb_server:{embed_url}"
                    })
                    
        return {
            "watching": "AniDB",
            "servers": {
                "sub": servers,
                "dub": []
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_anidb_source(link_id):
    try:
        if not link_id.startswith("anidb_server:"):
            return {"error": "Invalid link id"}, 400
            
        server_url = link_id.split("anidb_server:")[1]
        
        scraper = get_scraper()
        r = scraper.get(server_url, timeout=Config.SCRAPER_TIMEOUT)
        sources = []
        if r.status_code == 200:
            m3u8_match = re.search(r'file:\s*[\'\"]([^\'\"]+\.m3u8[^\'\"]*)[\'\"]', r.text)
            if m3u8_match:
                stream_url = m3u8_match.group(1)
                sources.append({
                    "file": stream_url,
                    "type": "hls",
                    "label": "Auto"
                })
                
        return {
            "embed_url": server_url,
            "skip": {},
            "sources": sources,
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500

