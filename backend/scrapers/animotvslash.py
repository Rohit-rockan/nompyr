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
        req = scraper.get(BASE_URL)
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            
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
                    image = img_tag.get('src') if img_tag else ""
                    if image and image.startswith('//'):
                        image = "https:" + image
                        
                    slug = href.rstrip('/').split('/')[-1]
                    url = f"/anime/animotvslash/{slug}"
                    
                    parsed_items.append({
                        "title": title,
                        "japanese_title": "",
                        "poster": image,
                        "url": url,
                        "slug": slug,
                        "current_episode": "",
                        "sub_episodes": "",
                        "dub_episodes": "",
                        "type": "TV"
                    })
                    
                if parsed_items:
                    if "latest" in section_title.lower() or "recent" in section_title.lower():
                        sections["latest_updates"].extend(parsed_items)
                        sections["top_trending"]["NOW"] = parsed_items
                        sections["top_trending"]["DAY"] = parsed_items
                        sections["top_trending"]["WEEK"] = parsed_items
                        sections["top_trending"]["MONTH"] = parsed_items
                    else:
                        sections["latest_updates"].extend(parsed_items)
    except Exception as e:
        return {"error": str(e)}, 500
    return sections

def search_anime_animotvslash(keyword, page=1):
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
            image = img_tag.get('src') if img_tag else ""
            if image and image.startswith('//'):
                image = "https:" + image
                
            slug = href.rstrip('/').split('/')[-1]
                
            url = f"/anime/animotvslash/{slug}"
            
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

def scrape_anime_info_animotvslash(slug):
    scraper = get_scraper()
    
    info_url = f"{BASE_URL}/anime/{slug}/"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return {"error": "Not found"}, 404
        
    soup = BeautifulSoup(req.text, 'html.parser')
    
    title_elem = soup.select_one('.infox h1')
    title = title_elem.text.strip() if title_elem else slug
    
    img_elem = soup.select_one('.thumb img')
    image = img_elem.get('src') if img_elem else ""
    if image and image.startswith('//'):
        image = "https:" + image
    
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

def fetch_episodes_animotvslash(slug):
    scraper = get_scraper()
    info_url = f"{BASE_URL}/anime/{slug}/"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return []
        
    soup = BeautifulSoup(req.text, 'html.parser')
    episodes_list = []
    
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
        
        episodes_list.append({
            "number": str(num),
            "slug": ep_slug,
            "title": ep_title,
            "japanese_title": "",
            "token": f"animotvslash:{ep_slug}",
            "has_sub": True,
            "has_dub": False
        })
        
    episodes_list.reverse()
    return episodes_list

def fetch_servers_animotvslash(ep_token):
    scraper = get_scraper()
    
    try:
        if not ep_token.startswith("animotvslash:"):
            return {"error": "Invalid token"}, 400
        episode_id = ep_token.split("animotvslash:")[1]
            
        url = f"{BASE_URL}/{episode_id}/"
        req = scraper.get(url)
        if req.status_code != 200:
            return {"error": "Not found"}, 404
            
        soup = BeautifulSoup(req.text, 'html.parser')
        iframe = soup.select_one('iframe')
        
        servers = []
        if iframe and iframe.get('src'):
            src = iframe.get('src')
            servers.append({
                "name": "HD Server (Animotvslash)",
                "server_id": src,
                "episode_id": episode_id,
                "link_id": f"animotvslash_server:{src}"
            })
            
        return {
            "watching": "Animotvslash",
            "servers": {
                "sub": servers,
                "dub": []
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_animotvslash_source(link_id):
    try:
        if not link_id.startswith("animotvslash_server:"):
            return {"error": "Invalid token"}, 400
        server_url = link_id.split("animotvslash_server:")[1]
        return {
            "embed_url": server_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
