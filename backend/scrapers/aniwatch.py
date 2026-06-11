import re
import base64
import requests
from bs4 import BeautifulSoup

ANIWATCH_URL = "https://aniwatch.co.at/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://aniwatch.co.at/",
}

def clean_url(href):
    if not href:
        return ""
    href = href.strip().strip("'\"")
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{ANIWATCH_URL.rstrip('/')}/{href.lstrip('/')}"

def scrape_home_aniwatch():
    try:
        response = requests.get(ANIWATCH_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Spotlight/Banners
        banner = []
        slides = soup.select(".swiper-slide") or soup.select(".des-slider .item") or soup.select(".slide-item")
        for slide in slides:
            img_tag = slide.find("img")
            title = img_tag.get("alt", "").strip() if img_tag else ""
            img_src = (img_tag.get("src") or img_tag.get("data-src") or "") if img_tag else ""
            if img_src:
                img_src = clean_url(img_src)
            a_tag = slide.select_one("a.btn") or slide.select_one("a")
            href = a_tag["href"] if a_tag else ""
            slug = href.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
            
            if title and slug:
                banner.append({
                    "title": title,
                    "japanese_title": "",
                    "description": "",
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

        # 2. Latest Updates
        latest = []
        latest_block = None
        for block in soup.select(".block_area"):
            header = block.select_one(".block_area-header") or block.select_one(".block-header") or block.select_one("h2")
            if header and "latest" in header.get_text().lower():
                latest_block = block
                break
        
        if latest_block:
            for item in latest_block.select(".flw-item"):
                title_tag = item.select_one(".film-name a")
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                url = clean_url(href)
                slug = url.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
                
                img_tag = item.select_one(".film-poster-img")
                poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
                poster = clean_url(poster)
                
                sub_eps = item.select_one(".tick-sub")
                sub = sub_eps.get_text(strip=True) if sub_eps else ""
                dub_eps = item.select_one(".tick-dub")
                dub = dub_eps.get_text(strip=True) if dub_eps else ""
                
                type_el = item.select_one(".fd-infor .fdi-item")
                anime_type = type_el.get_text(strip=True) if type_el else "TV"
                
                latest.append({
                    "title": title,
                    "japanese_title": "",
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "current_episode": "",
                    "sub_episodes": sub,
                    "dub_episodes": dub,
                    "type": anime_type,
                })

        # 3. Trending
        trending = {}
        trending_block = None
        for block in soup.select(".block_area"):
            header = block.select_one(".block_area-header") or block.select_one(".block-header") or block.select_one("h2")
            if header and "trending" in header.get_text().lower():
                trending_block = block
                break
        
        items = []
        if trending_block:
            for item in trending_block.select(".item"):
                num_span = item.select_one(".number span")
                rank = num_span.get_text(strip=True) if num_span else ""
                
                title_tag = item.select_one(".film-title a") or item.select_one(".film-poster")
                if not title_tag: continue
                
                href = title_tag.get("href", "")
                url = clean_url(href)
                slug = url.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
                
                img_tag = item.select_one(".film-poster-img")
                poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
                poster = clean_url(poster)
                
                title = img_tag.get("alt", "").strip() if img_tag else ""
                if not title:
                    title = title_tag.get_text(strip=True)
                
                items.append({
                    "rank": rank,
                    "title": title,
                    "japanese_title": "",
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "type": "TV",
                })
        trending["NOW"] = items
        trending["DAY"] = items
        trending["WEEK"] = items
        trending["MONTH"] = items

        # 4. Popular (New On Aniwatch)
        popular = []
        popular_block = None
        for block in soup.select(".block_area"):
            header = block.select_one(".block_area-header") or block.select_one(".block-header") or block.select_one("h2")
            if header and "new on" in header.get_text().lower():
                popular_block = block
                break
        
        if popular_block:
            for item in popular_block.select(".flw-item"):
                title_tag = item.select_one(".film-name a")
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                url = clean_url(href)
                slug = url.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
                
                img_tag = item.select_one(".film-poster-img")
                poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
                poster = clean_url(poster)
                
                sub_eps = item.select_one(".tick-sub")
                sub = sub_eps.get_text(strip=True) if sub_eps else ""
                dub_eps = item.select_one(".tick-dub")
                dub = dub_eps.get_text(strip=True) if dub_eps else ""
                
                type_el = item.select_one(".fd-infor .fdi-item")
                anime_type = type_el.get_text(strip=True) if type_el else "TV"
                
                popular.append({
                    "title": title,
                    "japanese_title": "",
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "sub_episodes": sub,
                    "dub_episodes": dub,
                    "type": anime_type,
                })

        # 5. Upcoming
        upcoming = []
        upcoming_block = None
        for block in soup.select(".block_area"):
            header = block.select_one(".block_area-header") or block.select_one(".block-header") or block.select_one("h2")
            if header and "upcoming" in header.get_text().lower():
                upcoming_block = block
                break
        
        if upcoming_block:
            for item in upcoming_block.select(".flw-item"):
                title_tag = item.select_one(".film-name a")
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                url = clean_url(href)
                slug = url.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
                
                img_tag = item.select_one(".film-poster-img")
                poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
                poster = clean_url(poster)
                
                upcoming.append({
                    "title": title,
                    "japanese_title": "",
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "sub_episodes": "",
                    "dub_episodes": "",
                    "type": "TV",
                })

        return {"banner": banner, "latest_updates": latest, "top_trending": trending, "popular": popular, "upcoming": upcoming}
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_aniwatch(keyword, page=1):
    try:
        if keyword:
            url = f"https://aniwatch.co.at/page/{page}/" if page > 1 else "https://aniwatch.co.at/"
            params = {"s": keyword}
        else:
            url = f"https://aniwatch.co.at/subbed-anime/page/{page}/" if page > 1 else "https://aniwatch.co.at/subbed-anime/"
            params = {}

        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        total_count = 0
        pagination = soup.select_one(".pagination")
        if pagination:
            page_links = pagination.find_all("a", class_="page-numbers")
            max_p = 1
            for a in page_links:
                txt = a.get_text(strip=True)
                if txt.isdigit():
                    max_p = max(max_p, int(txt))
            total_count = max_p * 18
        
        cards = soup.select(".flw-item")
        if not total_count:
            total_count = len(cards)

        results = []
        for item in cards:
            title_tag = item.select_one(".film-name a")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            url_clean = clean_url(href)
            slug = url_clean.split("aniwatch.co.at/")[-1].split("anime/")[-1].strip("/")
            
            img_tag = item.select_one(".film-poster-img")
            poster = (img_tag.get("data-src") or img_tag.get("src") or "") if img_tag else ""
            poster = clean_url(poster)
            
            sub_eps = item.select_one(".tick-sub")
            sub = sub_eps.get_text(strip=True) if sub_eps else ""
            dub_eps = item.select_one(".tick-dub")
            dub = dub_eps.get_text(strip=True) if dub_eps else ""
            
            type_el = item.select_one(".fd-infor .fdi-item")
            anime_type = type_el.get_text(strip=True) if type_el else "TV"
            
            results.append({
                "title": title,
                "japanese_title": "",
                "slug": slug,
                "url": url_clean,
                "poster": poster,
                "sub_episodes": sub,
                "dub_episodes": dub,
                "total_episodes": sub or "1",
                "year": "",
                "type": anime_type,
                "rating": "",
            })

        return {
            "total": total_count or len(results),
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_aniwatch(slug):
    try:
        if "-episode-" in slug or re.search(r'-ep-[0-9]+', slug):
            url = f"https://aniwatch.co.at/{slug}/"
        else:
            url = f"https://aniwatch.co.at/anime/{slug}/"
            
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        if "-episode-" in slug or re.search(r'-ep-[0-9]+', slug):
            detail_link = soup.find("a", string=lambda s: s and "view detail" in s.lower())
            if not detail_link:
                for a in soup.find_all("a", href=True):
                    if "/anime/" in a["href"]:
                        detail_link = a
                        break
            if detail_link:
                url = clean_url(detail_link["href"])
                response = requests.get(url, headers=HEADERS, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

        anime_id = ""
        shortlink = soup.find("link", rel="shortlink")
        if shortlink:
            href = shortlink.get("href", "")
            match = re.search(r'\?p=([0-9]+)', href)
            if match:
                anime_id = match.group(1)
        if not anime_id:
            match = re.search(r'data-animeid="([0-9]+)"', response.text)
            if match:
                anime_id = match.group(1)
        if not anime_id:
            anime_id = slug

        title_el = soup.select_one(".film-name") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""
        
        jp_title_el = soup.select_one(".alias-name") or soup.select_one(".film-name-alternative")
        jp_title = jp_title_el.get_text(strip=True) if jp_title_el else ""
        
        desc_el = soup.select_one(".film-description .text") or soup.select_one(".description")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        
        poster_el = soup.select_one(".film-poster img") or soup.select_one(".poster img")
        poster = ""
        if poster_el:
            poster = poster_el.get("data-src") or poster_el.get("src") or ""
        poster = clean_url(poster)

        detail = {}
        for block in soup.select(".item-title"):
            text = block.get_text(separator="|", strip=True)
            if ":" in text:
                k, v = text.split(":", 1)
                k = k.strip().lower().replace(" ", "_")
                detail[k] = v.strip()
                
        genres = []
        genres_el = soup.find(class_=lambda c: c and "genres" in c.lower()) or soup.select_one(".item-list")
        if genres_el:
            genres = [a.get_text(strip=True) for a in genres_el.find_all("a")]
        detail["genres"] = genres

        sub_eps = soup.select_one(".tick-sub").get_text(strip=True) if soup.select_one(".tick-sub") else ""
        dub_eps = soup.select_one(".tick-dub").get_text(strip=True) if soup.select_one(".tick-dub") else ""
        
        rating = detail.get("rating", "PG-13")
        score = detail.get("mal_score", "N/A")
        anime_type = detail.get("type", "TV")

        return {
            "ani_id": anime_id,
            "title": title,
            "japanese_title": jp_title,
            "description": desc,
            "poster": poster,
            "banner": poster,
            "sub_episodes": sub_eps,
            "dub_episodes": dub_eps,
            "type": anime_type,
            "rating": rating,
            "mal_score": score,
            "detail": detail,
            "seasons": [],
        }
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes_aniwatch(slug):
    try:
        info = scrape_anime_info_aniwatch(slug)
        if "error" in info:
            return info
        anime_id = info["ani_id"]
        
        url = f"https://aniwatch.co.at/wp-json/hianime/v1/episode/list/{anime_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("status") or not data.get("html"):
            return {"error": "WordPress endpoint returned empty/false status"}, 500
            
        soup = BeautifulSoup(data["html"], "html.parser")
        
        episodes = []
        for idx, ep in enumerate(soup.find_all("a")):
            href = ep.get("href", "")
            data_id = ep.get("data-id") or ""
            data_num = ep.get("data-number") or str(idx + 1)
            title = ep.get("title") or ep.get_text(strip=True)
            
            ep_text = ep.get_text(strip=True)
            if ep_text.startswith(data_num):
                title = ep_text[len(data_num):].strip()
            if not title:
                title = f"Episode {data_num}"
                
            ep_slug = href.split("aniwatch.co.at/")[-1].strip("/")
            
            episodes.append({
                "number": data_num,
                "slug": ep_slug or f"ep-{data_num}",
                "title": title,
                "japanese_title": "",
                "token": data_id,
                "has_sub": True,
                "has_dub": True,
            })
            
        return episodes
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_servers_aniwatch(ep_token):
    try:
        url = f"https://aniwatch.co.at/wp-json/hianime/v1/episode/servers/{ep_token}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("status") or not data.get("html"):
            return {"error": "WordPress endpoint returned empty/false status"}, 500
            
        soup = BeautifulSoup(data["html"], "html.parser")
        
        servers = {}
        for item in soup.select(".server-item"):
            srv_name = item.get("data-server-name") or item.select_one(".btn").get_text(strip=True)
            srv_type = item.get("data-type", "sub")
            srv_hash = item.get("data-hash", "")
            
            if not srv_hash: continue
            
            try:
                decoded_url = base64.b64decode(srv_hash).decode("utf-8")
            except Exception:
                continue
                
            if srv_type not in servers:
                servers[srv_type] = []
                
            servers[srv_type].append({
                "name": srv_name,
                "server_id": srv_type,
                "episode_id": ep_token,
                "link_id": decoded_url,
            })
            
        return {
            "watching": "VidSrc Player",
            "servers": servers
        }
    except Exception as e:
        return {"error": str(e)}, 500
