import requests
from bs4 import BeautifulSoup
import re
import urllib.parse


BASE_URL = "https://anineko.to"

def get_anineko_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": f"{BASE_URL}/",
    }

def scrape_home_anineko():
    url = f"{BASE_URL}/home"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        banner = []
        for slide in soup.select(".nv-hero-slide"):
            title_el = slide.select_one(".nv-hero-title")
            if not title_el: continue
            title = title_el.text.strip()
            
            img = slide.select_one(".nv-hero-bg")
            img_url = img["src"] if img else ""
            
            link = slide.select_one(".nv-hero-actions a")
            slug = link["href"].replace("/watch/", "") if link else ""
            
            desc_el = slide.select_one(".nv-hero-desc")
            desc = desc_el.text.strip() if desc_el else ""
            
            banner.append({
                "title": title,
                "japanese_title": "",
                "poster": img_url,
                "url": f"/anime/anineko/{slug}",
                "slug": slug,
                "current_episode": "",
                "sub_episodes": "",
                "dub_episodes": "",
                "type": "TV"
            })
            
        latest = []
        for item in soup.select("a.nv-latest-item"):
            img = item.select_one("img")
            img_url = img["src"] if img else ""
            title_el = item.select_one("strong")
            title = title_el.text.strip() if title_el else ""
            href = item.get("href", "")
            slug = href.split("/watch/")[-1].split("/ep-")[0] if "/watch/" in href else ""
            
            latest.append({
                "title": title,
                "japanese_title": "",
                "poster": img_url,
                "url": f"/anime/anineko/{slug}",
                "slug": slug,
                "current_episode": "",
                "sub_episodes": "",
                "dub_episodes": "",
                "type": "TV"
            })
            
        trending = []
        for item in soup.select("a.nv-trending-item"):
            img = item.select_one("img")
            img_url = img["src"] if img else ""
            title_el = item.select_one("strong")
            title = title_el.text.strip() if title_el else ""
            href = item.get("href", "")
            slug = href.split("/watch/")[-1] if "/watch/" in href else ""
            
            trending.append({
                "title": title,
                "japanese_title": "",
                "poster": img_url,
                "url": f"/anime/anineko/{slug}",
                "slug": slug,
                "current_episode": "",
                "sub_episodes": "",
                "dub_episodes": "",
                "type": "TV"
            })
            
        return {
            "banner": banner,
            "latest_updates": latest,
            "top_trending": {
                "NOW": trending,
                "DAY": trending,
                "WEEK": trending,
                "MONTH": trending
            },
            "popular": trending,
            "upcoming": []
        }
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_anineko(keyword, page=1):
    url = f"{BASE_URL}/browser?keyword={urllib.parse.quote(keyword)}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        results = []
        for card in soup.select(".nv-anime-card"):
            a = card.select_one("a.nv-anime-thumb")
            if not a: continue
            href = a.get("href", "")
            slug = href.split("/watch/")[-1] if "/watch/" in href else ""
            
            img = a.select_one("img")
            img_url = img["src"] if img else ""
            
            title_el = card.select_one(".nv-anime-title a")
            title = title_el.text.strip() if title_el else ""
            
            sub_count = 0
            dub_count = 0
            for badge in card.select(".nv-stat-badge"):
                text = badge.text.strip()
                if "CC" in text or "SUB" in text.upper():
                    nums = re.findall(r"\d+", text)
                    if nums: sub_count = int(nums[0])
                elif "DUB" in text.upper() or badge.select_one("svg"):
                    nums = re.findall(r"\d+", text)
                    if nums: dub_count = int(nums[0])
                    
            results.append({
                "title": title,
                "japanese_title": "",
                "slug": slug,
                "url": f"/anime/anineko/{slug}",
                "poster": img_url,
                "sub_episodes": str(sub_count),
                "dub_episodes": str(dub_count),
                "total_episodes": str(sub_count),
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

def scrape_anime_info_anineko(slug):
    url = f"{BASE_URL}/watch/{slug}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=10)
        if r.status_code != 200:
            return {"error": "Not found"}, 404
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        title_el = soup.select_one(".nv-info-main h1")
        title = title_el.text.strip() if title_el else slug
        
        img_el = soup.select_one(".nv-info-poster img")
        img_url = img_el["src"] if img_el else ""
        
        desc_el = soup.select_one(".nv-info-synopsis p")
        if not desc_el:
            desc_el = soup.select_one(".nv-info-desc")
        desc = desc_el.text.strip() if desc_el else ""
        
        return {
            "ani_id": slug,
            "title": title,
            "japanese_title": "",
            "description": desc,
            "poster": img_url,
            "banner": img_url,
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

def fetch_episodes_anineko(slug):
    url = f"{BASE_URL}/watch/{slug}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=10)
        if r.status_code != 200:
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        episodes = []
        for ep_card in soup.select(".nv-info-episode-item"):
            ep_link = ep_card.select_one("a.nv-info-episode-main")
            if not ep_link: continue
            ep_id = ep_link["href"].split("/watch/")[-1] 
            num_text = ep_link.select_one("strong").text.strip() if ep_link.select_one("strong") else ""
            num = num_text.replace("Episode", "").strip()
            if not num: num = ep_id.split("-")[-1]
            
            episodes.append({
                "number": str(num),
                "slug": ep_id,
                "title": f"Episode {num}",
                "japanese_title": "",
                "token": f"anineko:{ep_id}",
                "has_sub": True,
                "has_dub": False
            })
            
        return episodes
    except Exception as e:
        return []

def fetch_servers_anineko(ep_token):
    try:
        if not ep_token.startswith("anineko:"):
            return {"error": "Invalid token"}, 400
        episode_id = ep_token.split("anineko:")[1]
        
        url = f"{BASE_URL}/watch/{episode_id}"
        r = requests.get(url, headers=get_anineko_headers(), timeout=10)
        if r.status_code != 200:
            return {"error": "Not found"}, 404
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        sub_servers = []
        dub_servers = []
        
        for panel in soup.select(".nv-server-panel"):
            kind = panel.get("data-id", "sub").lower()
            kind = "dub" if "dub" in kind else "sub"
            
            for btn in panel.select(".nv-server-btn"):
                data_video = btn.get("data-video", "")
                if not data_video: continue
                
                name = btn.contents[0].strip() if btn.contents else ""
                
                server = {
                    "name": name,
                    "server_id": data_video,
                    "episode_id": episode_id,
                    "link_id": f"anineko_server:{data_video}"
                }
                
                if kind == "sub":
                    sub_servers.append(server)
                else:
                    dub_servers.append(server)
        
        return {
            "watching": "Anineko",
            "servers": {
                "sub": sub_servers,
                "dub": dub_servers
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_anineko_source(link_id):
    try:
        if not link_id.startswith("anineko_server:"):
            return {"error": "Invalid token"}, 400
        server_url = link_id.split("anineko_server:")[1]
        return {
            "embed_url": server_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
