import requests
from bs4 import BeautifulSoup
import base64
import re
import traceback

ANIKOTO_URL = "https://anikototv.to/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://anikototv.to/",
}

def clean_url(href):
    if not href:
        return ""
    href = href.strip().strip("'\"")
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{ANIKOTO_URL.rstrip('/')}/{href.lstrip('/')}"

def scrape_home_anikototv():
    try:
        response = requests.get(ANIKOTO_URL + "home", headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        banner = []
        slides = soup.select(".swiper-slide.item")
        for slide in slides:
            title_tag = slide.select_one(".title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            img_div = slide.select_one(".image div")
            img_src = ""
            if img_div and "background-image: url" in img_div.get("style", ""):
                m = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_div.get("style", ""))
                if m:
                    img_src = clean_url(m.group(1))
                    
            a_tag = slide.select_one("a.play")
            href = a_tag["href"] if a_tag else ""
            slug = href.split("anikototv.to/")[-1].split("watch/")[-1].strip("/")
            
            desc_tag = slide.select_one(".synopsis")
            description = desc_tag.get_text(strip=True) if desc_tag else ""
            
            if title and slug:
                banner.append({
                    "title": title,
                    "japanese_title": title_tag.get("data-jp", "") if title_tag else "",
                    "description": description,
                    "poster": img_src,
                    "url": clean_url(href),
                    "slug": slug,
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "type": "TV",
                    "genres": "",
                    "rating": "PG-13",
                    "release": "",
                    "quality": "HD",
                })
        
        latest = []
        other_items = [i for i in soup.select(".item") if "swiper-slide" not in i.get("class", [])]
        for item in other_items:
            title_tag = item.select_one(".name")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            url = clean_url(href)
            slug = url.split("anikototv.to/")[-1].split("watch/")[-1].split("/")[0].strip("/")
            
            img_tag = item.select_one(".ani.poster img")
            poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
            poster = clean_url(poster)
            
            sub_eps = item.select_one(".ep-status.sub span")
            sub = sub_eps.get_text(strip=True) if sub_eps else ""
            dub_eps = item.select_one(".ep-status.dub span")
            dub = dub_eps.get_text(strip=True) if dub_eps else ""
            
            type_el = item.select_one(".meta .right")
            anime_type = type_el.get_text(strip=True) if type_el else "TV"
            
            latest.append({
                "title": title,
                "japanese_title": title_tag.get("data-jp", ""),
                "poster": poster,
                "url": url,
                "slug": slug,
                "current_episode": "",
                "sub_episodes": sub,
                "dub_episodes": dub,
                "type": anime_type,
            })
            
        return {
            "banner": banner, 
            "latest_updates": latest,
            "top_trending": {
                "NOW": [],
                "DAY": [],
                "WEEK": [],
                "MONTH": []
            },
            "popular": [],
            "upcoming": []
        }
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_anikototv(keyword, page=1):
    try:
        url = f"{ANIKOTO_URL}filter?keyword={requests.utils.quote(keyword)}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        results = []
        for item in soup.select(".item"):
            title_tag = item.select_one(".name")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            item_url = clean_url(href)
            slug = item_url.split("anikototv.to/")[-1].split("watch/")[-1].split("/")[0].strip("/")
            
            img_tag = item.select_one(".ani.poster img")
            poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
            poster = clean_url(poster)
            
            sub_eps = item.select_one(".ep-status.sub span")
            sub = sub_eps.get_text(strip=True) if sub_eps else ""
            dub_eps = item.select_one(".ep-status.dub span")
            dub = dub_eps.get_text(strip=True) if dub_eps else ""
            
            results.append({
                "title": title,
                "japanese_title": title_tag.get("data-jp", ""),
                "poster": poster,
                "url": item_url,
                "slug": slug,
                "sub_episodes": sub,
                "dub_episodes": dub,
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

def scrape_anime_info_anikototv(slug):
    try:
        url = f"{ANIKOTO_URL}watch/{slug}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        title_tag = soup.select_one(".film-name")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        img_tag = soup.select_one(".film-poster-img")
        poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
        poster = clean_url(poster)
        
        desc_tag = soup.select_one(".film-description .text")
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        
        return {
            "ani_id": slug,
            "title": title,
            "japanese_title": "",
            "description": description,
            "poster": poster,
            "banner": poster,
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

def _get_data_id(slug):
    url = f"{ANIKOTO_URL}watch/{slug}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    watch_main = soup.select_one("#watch-main")
    return watch_main.get("data-id") if watch_main else None

def fetch_episodes_anikototv(slug):
    try:
        data_id = _get_data_id(slug)
        if not data_id:
            return []
            
        ajax_url = f"{ANIKOTO_URL}ajax/episode/list/{data_id}"
        r = requests.get(ajax_url, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"}, timeout=15)
        r.raise_for_status()
        
        html = r.json().get("result", "")
        soup = BeautifulSoup(html, "html.parser")
        
        eps = []
        for a in soup.select("ul.episodes li a") or soup.find_all("a", {"data-ids": True}):
            data_num = a.get("data-num")
            data_ids = a.get("data-ids") # THIS IS WHAT WE NEED
            
            name_el = a.select_one(".name")
            title = name_el.get_text(strip=True) if name_el else a.get_text(strip=True)
            
            eps.append({
                "number": data_num,
                "slug": data_ids,
                "title": title,
                "japanese_title": "",
                "token": f"anikototv:{data_ids}",
                "has_sub": True,
                "has_dub": False
            })
            
        return eps
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_servers_anikototv(ep_token):
    try:
        if not ep_token.startswith("anikototv:"):
            return {"error": "Invalid episode token"}, 400
        episode_id = ep_token.split("anikototv:")[1]
            
        ajax_url = f"{ANIKOTO_URL}ajax/server/list?servers={episode_id}"
        r = requests.get(ajax_url, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"}, timeout=15)
        r.raise_for_status()
        
        data = r.json()
        if data.get("status") != 200:
            return {"error": f"Bad status: {data.get('status')}"}, 400
            
        html = data.get("result", "")
        soup = BeautifulSoup(html, "html.parser")
        
        sub_servers = []
        dub_servers = []
        
        for item in soup.select(".servers .type"):
            type_type = item.get("data-type") # sub, dub
            
            for li in item.select("li"):
                server_name = li.text.strip()
                data_link_id = li.get("data-link-id")
                
                server_obj = {
                    "name": server_name,
                    "server_id": data_link_id,
                    "episode_id": episode_id,
                    "link_id": f"anikototv_server:{data_link_id}"
                }
                
                if type_type == "dub":
                    dub_servers.append(server_obj)
                else:
                    sub_servers.append(server_obj)
                    
        return {
            "watching": "AnikotoTV",
            "servers": {
                "sub": sub_servers,
                "dub": dub_servers
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_anikototv_source(link_id):
    try:
        if not link_id.startswith("anikototv_server:"):
            return {"error": "Invalid link id"}, 400
        server_id = link_id.split("anikototv_server:")[1]
            
        padded = server_id + "=" * ((4 - len(server_id) % 4) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        
        return {
            "embed_url": decoded,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
