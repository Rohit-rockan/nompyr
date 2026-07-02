import requests
from bs4 import BeautifulSoup
from config import Config
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
        r = requests.get(url, headers=get_anineko_headers(), timeout=Config.SCRAPER_TIMEOUT)
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
                "id": slug,
                "title": title,
                "img": img_url,
                "description": desc,
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
                "id": slug,
                "title": title,
                "img": img_url,
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
                "id": slug,
                "title": title,
                "img": img_url,
                "rank": item.select_one(".nv-rank").text.strip() if item.select_one(".nv-rank") else ""
            })
            
        return {
            "banner": banner,
            "latest_updates": latest,
            "top_trending": trending,
        }
    except Exception as e:
        print(f"anineko scrape_home error: {e}")
        return {"error": str(e)}

def search_anineko(keyword, page=1):
    url = f"{BASE_URL}/browser?keyword={urllib.parse.quote(keyword)}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=Config.SCRAPER_TIMEOUT)
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
                "id": slug,
                "title": title,
                "img": img_url,
                "sub": sub_count,
                "dub": dub_count,
            })
            
        return {
            "data": results,
            "page": page,
            "total_pages": 1, 
        }
    except Exception as e:
        print(f"anineko search error: {e}")
        return {"error": str(e)}

def scrape_anime_info_anineko(slug):
    url = f"{BASE_URL}/watch/{slug}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        title_el = soup.select_one(".nv-info-main h1")
        title = title_el.text.strip() if title_el else slug
        
        img_el = soup.select_one(".nv-info-poster img")
        img_url = img_el["src"] if img_el else ""
        
        desc_el = soup.select_one(".nv-info-synopsis p")
        if not desc_el:
            desc_el = soup.select_one(".nv-info-desc")
        desc = desc_el.text.strip() if desc_el else ""
        
        # Tags/Genres
        genres = []
        # Usually they don't explicitly list genres in the info header in Anineko, but let's grab what we can
        
        # Episodes
        episodes = []
        for ep_card in soup.select(".nv-info-episode-item"):
            ep_link = ep_card.select_one("a.nv-info-episode-main")
            if not ep_link: continue
            ep_id = ep_link["href"].split("/watch/")[-1] # will look like slug/ep-1
            num_text = ep_link.select_one("strong").text.strip() if ep_link.select_one("strong") else ""
            num = num_text.replace("Episode", "").strip()
            if not num: num = ep_id.split("-")[-1]
            
            episodes.append({
                "id": ep_id,
                "number": int(num) if num.isdigit() else float(num) if '.' in num else num,
                "title": f"Episode {num}"
            })
            
        return {
            "id": slug,
            "title": title,
            "img": img_url,
            "description": desc,
            "episodes": episodes
        }
    except Exception as e:
        print(f"anineko info error: {e}")
        return {"error": str(e)}

def fetch_episodes_anineko(slug):
    res = scrape_anime_info_anineko(slug)
    if "error" in res:
        return res
    return {"episodes": res.get("episodes", [])}

def fetch_servers_anineko(ep_token):
    # ep_token is expected to be `slug/ep-1`
    url = f"{BASE_URL}/watch/{ep_token}"
    try:
        r = requests.get(url, headers=get_anineko_headers(), timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        servers = []
        # group by sub/dub tab
        for panel in soup.select(".nv-server-panel"):
            kind = panel.get("data-id", "sub").lower()
            kind = "dub" if "dub" in kind else "sub"
            
            for btn in panel.select(".nv-server-btn"):
                data_video = btn.get("data-video", "")
                if not data_video: continue
                
                # Server name is usually directly inside the button text before span
                name = btn.contents[0].strip() if btn.contents else ""
                
                servers.append({
                    "id": data_video, # raw URL is the ID!
                    "name": f"{name} ({kind})".strip(),
                    "type": kind
                })
        
        return {"servers": servers}
    except Exception as e:
        print(f"anineko servers error: {e}")
        return {"error": str(e)}

def resolve_source_anineko(source_id):
    # The source_id is directly the URL provided in data-video!
    return {
        "sources": [],
        "link": source_id,
        "direct": False
    }
