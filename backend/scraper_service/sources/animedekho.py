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
    
    sections = {
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
    
    try:
        req = scraper.get(f"{BASE_URL}/home/")
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            
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
                
                media_type = "Movie" if "/movie" in href else "TV"
                
                url = f"/anime/animedekho/{slug}"
                
                bg_div = item.select_one('.bg')
                image = ""
                if bg_div and bg_div.get('style'):
                    m = re.search(r'url\((.*?)\)', bg_div.get('style'))
                    if m:
                        image = m.group(1).strip("'\"")
                        
                parsed_items.append({
                    "title": title,
                    "japanese_title": "",
                    "poster": image,
                    "url": url,
                    "slug": slug,
                    "current_episode": "",
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "type": media_type
                })
                
            if parsed_items:
                sections["latest_updates"].extend(parsed_items)
                sections["top_trending"]["NOW"] = parsed_items
                sections["top_trending"]["DAY"] = parsed_items
                sections["top_trending"]["WEEK"] = parsed_items
                sections["top_trending"]["MONTH"] = parsed_items
    except Exception as e:
        return {"error": str(e)}, 500
    return sections

def search_anime_animedekho(keyword, page=1):
    scraper = get_scraper()
    try:
        req = scraper.get(f"{BASE_URL}/?s={keyword}")
        if req.status_code != 200:
            return {
                "total": 0,
                "page": page,
                "per_page": 0,
                "results": []
            }
            
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
            image = ""
            if bg_div and bg_div.get('style'):
                m = re.search(r'url\((.*?)\)', bg_div.get('style'))
                if m:
                    image = m.group(1).strip("'\"")
                    
            results.append({
                "title": title,
                "japanese_title": "",
                "slug": slug,
                "url": url,
                "poster": image,
                "sub_episodes": "",
                "dub_episodes": "",
                "total_episodes": "",
                "year": "",
                "type": media_type,
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

def scrape_anime_info_animedekho(slug):
    scraper = get_scraper()
    
    urls_to_try = [
        f"{BASE_URL}/series-hindi/{slug}/",
        f"{BASE_URL}/movie-hindi/{slug}/",
        f"{BASE_URL}/series/{slug}/",
        f"{BASE_URL}/movie/{slug}/"
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
        return {"error": "Not found"}, 404
        
    title_elem = soup.select_one('.entry-title')
    title = title_elem.text.strip() if title_elem else slug
    
    img_elem = soup.select_one('figure img')
    image = img_elem.get('src') if img_elem else ""
    
    desc_elem = soup.select_one('.entry-content')
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
        "type": "Movie" if "/movie" in final_url else "TV",
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

def fetch_episodes_animedekho(slug):
    scraper = get_scraper()
    urls_to_try = [
        f"{BASE_URL}/series-hindi/{slug}/",
        f"{BASE_URL}/movie-hindi/{slug}/",
        f"{BASE_URL}/series/{slug}/",
        f"{BASE_URL}/movie/{slug}/"
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
        return []
        
    title_elem = soup.select_one('.entry-title')
    title = title_elem.text.strip() if title_elem else slug
    
    episodes = []
    
    if "/movie" in final_url:
        episodes.append({
            "number": "1",
            "slug": slug,
            "title": title,
            "japanese_title": "",
            "token": f"animedekho:{slug}",
            "has_sub": True,
            "has_dub": False
        })
    else:
        episodes_blocks = soup.select('div > div:has(h3.title) + div a.btn.sm')
        for ep_btn in episodes_blocks:
            ep_href = ep_btn.get('href', '')
            ep_slug = ep_href.rstrip('/').split('/')[-1]
            
            parent = ep_btn.parent.parent
            title_e = parent.select_one('h3.title')
            ep_title = title_e.text.strip() if title_e else ep_slug
            
            num = ep_slug
            m = re.search(r'-(\d+)x(\d+)$', ep_slug)
            if m:
                num = m.group(2)
                
            episodes.append({
                "number": str(num),
                "slug": ep_slug,
                "title": ep_title,
                "japanese_title": "",
                "token": f"animedekho:{ep_slug}",
                "has_sub": True,
                "has_dub": False
            })
            
    return episodes

def fetch_servers_animedekho(ep_token):
    try:
        if not ep_token.startswith("animedekho:"):
            return {"error": "Invalid token"}, 400
        episode_id = ep_token.split("animedekho:")[1]
        
        scraper = get_scraper()
        url = f"{BASE_URL}/epi/{episode_id}/"
        req = scraper.get(url)
        
        if req.status_code != 200:
            url = f"{BASE_URL}/movie-hindi/{episode_id}/"
            req = scraper.get(url)
            if req.status_code != 200:
                return {"error": "Not found"}, 404
                
        soup = BeautifulSoup(req.text, 'html.parser')
        iframes = soup.select('iframe')
        
        servers = []
        for i, iframe in enumerate(iframes):
            src = iframe.get('src')
            if src:
                servers.append({
                    "name": f"Server {i+1} (Animedekho)",
                    "server_id": src,
                    "episode_id": episode_id,
                    "link_id": f"animedekho_server:{src}"
                })
                
        return {
            "watching": "Animedekho",
            "servers": {
                "sub": servers,
                "dub": []
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_animedekho_source(link_id):
    try:
        if not link_id.startswith("animedekho_server:"):
            return {"error": "Invalid token"}, 400
        server_url = link_id.split("animedekho_server:")[1]
        
        return {
            "embed_url": server_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
