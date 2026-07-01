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
            
            # The background image is in the style of div inside .image
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
        
        # Latest updates
        latest = []
        # exclude swiper slides
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
            
        return {"success": True, "data": {"banner": banner, "latest_updates": latest}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_anikototv(query):
    try:
        url = f"{ANIKOTO_URL}filter?keyword={requests.utils.quote(query)}"
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
                "type": "TV",
            })
        
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        
        info = {
            "title": title,
            "japanese_title": "",
            "poster": poster,
            "description": description,
            "url": url,
            "slug": slug,
            "type": "TV",
            "release": "",
            "status": "",
            "genres": [],
        }
        
        # The main data-id for the anime is in a div
        watch_main = soup.select_one("#watch-main")
        data_id = watch_main.get("data-id") if watch_main else None
        
        return {"success": True, "data": info, "data_id": data_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_episodes_anikototv(slug):
    # To fetch episodes, we first need the data_id
    info_res = scrape_anime_info_anikototv(slug)
    if not info_res.get("success"):
        return info_res
    
    data_id = info_res.get("data_id")
    if not data_id:
        return {"success": False, "error": "Could not find data-id on watch page"}
        
    try:
        ajax_url = f"{ANIKOTO_URL}ajax/episode/list/{data_id}"
        r = requests.get(ajax_url, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"}, timeout=15)
        r.raise_for_status()
        
        html = r.json().get("result", "")
        soup = BeautifulSoup(html, "html.parser")
        
        eps = []
        for a in soup.select("ul.episodes li a") or soup.find_all("a", {"data-ids": True}):
            data_num = a.get("data-num")
            data_ids = a.get("data-ids") # THIS IS WHAT WE NEED
            data_ep_id = a.get("data-id")
            
            # Text could be in a child div like .name
            name_el = a.select_one(".name")
            title = name_el.get_text(strip=True) if name_el else a.get_text(strip=True)
            
            eps.append({
                "number": data_num,
                "title": title,
                "id": data_ids, # we pass data-ids as the episode id
                "url": ""
            })
            
        return {"success": True, "data": eps}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_servers_anikototv(episode_id):
    # episode_id here is data_ids
    try:
        ajax_url = f"{ANIKOTO_URL}ajax/server/list?servers={episode_id}"
        r = requests.get(ajax_url, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"}, timeout=15)
        r.raise_for_status()
        
        data = r.json()
        if data.get("status") != 200:
            return {"success": False, "error": f"Bad status: {data.get('status')}"}
            
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
                    "server": server_name,
                    "id": data_link_id, # THIS is what we decode!
                    "type": type_type,
                    "url": ""
                }
                
                if type_type == "dub":
                    dub_servers.append(server_obj)
                else:
                    sub_servers.append(server_obj)
                    
        return {"success": True, "data": {"sub": sub_servers, "dub": dub_servers}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def resolve_source_anikototv(server_id, episode_id=None):
    # server_id is the data-link-id
    try:
        padded = server_id + "=" * ((4 - len(server_id) % 4) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        
        return {
            "success": True,
            "data": {
                "source_url": decoded, # Emphasize that it is an iframe URL!
                "headers": {},
                "subtitles": []
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("Testing Home...")
    home = scrape_home_anikototv()
    print("Spotlight:", len(home.get("data", {}).get("spotlight", [])))
    print("Latest:", len(home.get("data", {}).get("latest", [])))
    
    print("\\nTesting Search...")
    search = search_anikototv("naruto")
    print("Found:", len(search.get("data", [])))
    if search.get("data"):
        print("First:", search["data"][0])
        
    print("\\nTesting Episodes...")
    # naruto-shippuuden-movie-6-road-to-ninja-w2wqq
    # solo-leveling-ilh08
    eps = fetch_episodes_anikototv("solo-leveling-ilh08")
    print("Found:", len(eps.get("data", [])))
    if eps.get("data"):
        print("First:", eps["data"][0])
        
        print("\\nTesting Servers...")
        servers = fetch_servers_anikototv(eps["data"][0]["id"])
        print("Sub servers:", len(servers.get("data", {}).get("sub", [])))
        if servers.get("data", {}).get("sub"):
            print("First:", servers["data"]["sub"][0])
            
            print("\\nTesting Source...")
            src = resolve_source_anikototv(servers["data"]["sub"][0]["id"])
            print("Resolved URL:", src.get("data", {}).get("source_url"))
