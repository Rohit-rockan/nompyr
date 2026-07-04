import re
import requests
from bs4 import BeautifulSoup

ANIMEKAI_URL = "https://animekai.be/"
ANIMEKAI_HOME_URL = "https://animekai.be/home"
ANIMEKAI_SEARCH_URL = "https://animekai.be/ajax/anime/search"
ANIMEKAI_EPISODES_URL = "https://animekai.be/ajax/episodes/list"
ANIMEKAI_SERVERS_URL = "https://animekai.be/ajax/links/list"
ANIMEKAI_LINKS_VIEW_URL = "https://animekai.be/ajax/links/view"

ENCDEC_URL = "https://enc-dec.app/api/enc-kai"
ENCDEC_DEC_KAI = "https://enc-dec.app/api/dec-kai"
ENCDEC_DEC_MEGA = "https://enc-dec.app/api/dec-mega"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://animekai.be/",
}

AJAX_HEADERS = {
    **HEADERS,
    "X-Requested-With": "XMLHttpRequest"
}

def clean_url(href):
    if not href:
        return ""
    href = href.strip().strip("'\"")
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{ANIMEKAI_URL.rstrip('/')}/{href.lstrip('/')}"

def encode_token(text):
    try:
        r = requests.get(ENCDEC_URL, params={"text": text}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("result") if data.get("status") == 200 else None
    except Exception as e:
        return {"error": str(e)}, 500

def decode_kai(text):
    try:
        r = requests.post(ENCDEC_DEC_KAI, json={"text": text}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("result") if data.get("status") == 200 else None
    except Exception as e:
        return {"error": str(e)}, 500

def decode_mega(text):
    try:
        r = requests.post(ENCDEC_DEC_MEGA, json={
            "text": text,
            "agent": HEADERS["User-Agent"],
        }, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("result") if data.get("status") == 200 else None
    except Exception as e:
        return {"error": str(e)}, 500

def parse_info_spans(info_el):
    sub_eps = ""
    dub_eps = ""
    anime_type = ""
    for span in info_el.find_all("span") if info_el else []:
        cls = span.get("class", [])
        if "sub" in cls:
            sub_eps = span.get_text(strip=True)
        elif "dub" in cls:
            dub_eps = span.get_text(strip=True)
        else:
            b_tag = span.find("b")
            if b_tag:
                anime_type = span.get_text(strip=True)
    return sub_eps, dub_eps, anime_type

def scrape_most_searched():
    try:
        response = requests.get(ANIMEKAI_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        most_searched_div = soup.find("div", class_="most_searched")
        if not most_searched_div:
            most_searched_div = soup.find("div", class_="most-searched")

        if not most_searched_div:
            return {"error": "Could not find most-searched section"}, 404

        results = []
        for link in most_searched_div.find_all("a"):
            name = link.get_text(strip=True)
            href = link.get("href", "")
            keyword = href.split("keyword=")[-1].replace("+", " ") if "keyword=" in href else ""
            if name:
                results.append({
                    "name": name,
                    "keyword": keyword,
                    "search_url": f"{ANIMEKAI_URL.rstrip('/')}{href}" if href.startswith("/") else href,
                })
        return results
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime(keyword, page=1):
    try:
        url = "https://animekai.be/browse"
        params = {"page": page}
        if keyword:
            params["keyword"] = keyword
            
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Parse total count
        total_count = 0
        count_el = soup.find(class_=lambda c: c and "count" in c)
        if count_el:
            match = re.search(r'([\d,]+)', count_el.get_text())
            if match:
                total_count = int(match.group(1).replace(",", ""))
        if not total_count:
            match = re.search(r'([\d,]+)\s+anime', soup.text, re.IGNORECASE)
            if match:
                total_count = int(match.group(1).replace(",", ""))

        results = []
        for item in soup.find_all(class_="aitem"):
            title_tag = item.find("a", class_="title")
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            japanese_title = title_tag.get("data-jp", "")
            href = title_tag.get("href", "")
            url_clean = clean_url(href)
            slug = url_clean.split("/watch/")[-1].split("?")[0].split("#")[0].strip("/")
            
            poster_tag = item.select_one(".poster img")
            poster = ""
            if poster_tag:
                poster = poster_tag.get("data-src") or poster_tag.get("src") or ""
            poster = clean_url(poster)
            
            sub, dub = "", ""
            anime_type = ""
            for span in item.select(".info span"):
                cls = span.get("class", [])
                if "sub" in cls: sub = span.get_text(strip=True)
                elif "dub" in cls: dub = span.get_text(strip=True)
                else:
                    b_tag = span.find("b")
                    if b_tag: anime_type = span.get_text(strip=True)
            
            if title:
                results.append({
                    "title": title,
                    "japanese_title": japanese_title,
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

def scrape_home():
    try:
        response = requests.get(ANIMEKAI_HOME_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        banner = []
        for slide in soup.select(".swiper-slide"):
            style = slide.get("style", "")
            bg_image = style.split("url(")[1].split(")")[0] if "url(" in style else ""
            bg_image = clean_url(bg_image)
            title_tag = slide.select_one("p.title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            japanese_title = title_tag.get("data-jp", "") if title_tag else ""
            description = slide.select_one("p.desc").get_text(strip=True) if slide.select_one("p.desc") else ""
            
            sub, dub, anime_type = parse_info_spans(slide.select_one(".info"))
            
            genres = ""
            info_el = slide.select_one(".info")
            if info_el:
                for span in info_el.find_all("span"):
                    if not span.get("class") and not span.find("b"):
                        text = span.get_text(strip=True)
                        if text and not text.isdigit(): genres = text

            rating, release, quality = "", "", ""
            mics = slide.select_one(".mics")
            if mics:
                for div in mics.find_all("div", recursive=False):
                    l, v = div.select_one("div"), div.select_one("span")
                    if l and v:
                        lbl = l.get_text(strip=True).lower()
                        if lbl == "rating": rating = v.get_text(strip=True)
                        elif lbl == "release": release = v.get_text(strip=True)
                        elif lbl == "quality": quality = v.get_text(strip=True)

            if title:
                watch_btn = slide.select_one('a.watch-btn')
                href = watch_btn.get('href', '') if watch_btn else ""
                url = clean_url(href)
                slug = url.split("/watch/")[-1].split("?")[0].split("#")[0].strip("/")
                banner.append({
                    "title": title,
                    "japanese_title": japanese_title,
                    "description": description,
                    "poster": bg_image,
                    "url": url,
                    "slug": slug,
                    "sub_episodes": sub,
                    "dub_episodes": dub,
                    "type": anime_type,
                    "genres": genres,
                    "rating": rating,
                    "release": release,
                    "quality": quality,
                })

        latest = []
        for item in soup.select(".aitem-wrapper.regular .aitem"):
            title_tag = item.select_one("a.title")
            href = item.select_one("a.poster").get("href", "") if item.select_one("a.poster") else ""
            episode = href.split("#ep=")[-1] if "#ep=" in href else ""
            href = href.split("#ep=")[0]
            url = clean_url(href)
            slug = url.split("/watch/")[-1].split("?")[0].split("#")[0].strip("/")
            
            sub, dub, anime_type = parse_info_spans(item.select_one(".info"))
            
            poster_tag = item.select_one(".poster img")
            poster = ""
            if poster_tag:
                poster = poster_tag.get("data-src") or poster_tag.get("src") or ""
            poster = clean_url(poster)
            
            if title_tag:
                latest.append({
                    "title": title_tag.get_text(strip=True),
                    "japanese_title": title_tag.get("data-jp", ""),
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "current_episode": episode,
                    "sub_episodes": sub,
                    "dub_episodes": dub,
                    "type": anime_type,
                })

        trending = {}
        container = soup.select_one("#trending-anime .aitem-col.top-anime") or soup.select_one(".aitem-col.top-anime")
        items = []
        if container:
            for item in container.find_all(class_="aitem"):
                style = item.get("style", "")
                poster = style.split("url(")[1].split(")")[0] if "url(" in style else ""
                poster = clean_url(poster)
                sub, dub, anime_type = parse_info_spans(item.select_one(".info"))
                
                title_tag = item.select_one(".detail .title") or item.select_one("a.title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                jp_title = title_tag.get("data-jp", "") if title_tag else ""
                href = title_tag.get("href", "") if title_tag else ""
                url = clean_url(href)
                slug = url.split("/watch/")[-1].split("?")[0].split("#")[0].strip("/")
                
                items.append({
                    "rank": item.select_one(".num").get_text(strip=True) if item.select_one(".num") else "",
                    "title": title,
                    "japanese_title": jp_title,
                    "poster": poster,
                    "url": url,
                    "slug": slug,
                    "sub_episodes": sub,
                    "dub_episodes": dub,
                    "type": anime_type,
                })
        trending["NOW"] = items
        trending["DAY"] = items
        trending["WEEK"] = items
        trending["MONTH"] = items

        return {"banner": banner, "latest_updates": latest, "top_trending": trending}
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info(slug):
    try:
        url = f"https://animekai.be/watch/{slug}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        ani_id = ""
        for script in soup.find_all("script"):
            content = script.string or script.text or ""
            match = re.search(r'var\s+_cmAnimeId\s*=\s*([0-9]+)\s*;', content)
            if match:
                ani_id = match.group(1)
                break
        if not ani_id:
            rate_box = soup.select_one(".rate-box")
            if rate_box:
                ani_id = rate_box.get("data-id", "")
        if not ani_id:
            ani_id = slug

        info_el = soup.select_one(".main-entity .info")
        sub, dub, atype = parse_info_spans(info_el)
        
        detail = {}
        for div in soup.select(".detail > div > div"):
            text = div.get_text(separator="|", strip=True)
            if ":" in text:
                k, v = text.split(":", 1)
                k = k.strip().lower().replace(" ", "_").replace(":", "")
                links = div.select("span a")
                detail[k] = [a.get_text(strip=True) for a in links] if links else v.strip().strip("|")

        seasons = []
        for s in soup.select(".swiper-wrapper.season .aitem"):
            is_active = "active" in s.get("class", [])
            d = s.select_one(".detail")
            img_tag = s.select_one("img")
            s_poster = ""
            if img_tag:
                s_poster = img_tag.get("data-src") or img_tag.get("src") or ""
            s_poster = clean_url(s_poster)
            
            seasons.append({
                "title": d.select_one("span").get_text(strip=True) if d else "",
                "episodes": d.select_one(".btn").get_text(strip=True) if d else "",
                "poster": s_poster,
                "url": clean_url(s.select_one('a.poster').get('href', '')) if s.select_one('a.poster') else "",
                "active": is_active,
            })

        bg_el = soup.select_one(".watch-section-bg")
        banner = bg_el.get("style", "").split("url(")[1].split(")")[0] if bg_el and "url(" in bg_el.get("style", "") else ""
        banner = clean_url(banner)

        poster_tag = soup.select_one(".poster img")
        poster = ""
        if poster_tag:
            poster = poster_tag.get("data-src") or poster_tag.get("src") or ""
        poster = clean_url(poster)

        return {
            "ani_id": ani_id,
            "title": soup.select_one("h1.title").get_text(strip=True) if soup.select_one("h1.title") else "",
            "japanese_title": soup.select_one("h1.title").get("data-jp", "") if soup.select_one("h1.title") else "",
            "description": soup.select_one(".desc").get_text(strip=True) if soup.select_one(".desc") else "",
            "poster": poster,
            "banner": banner,
            "sub_episodes": sub,
            "dub_episodes": dub,
            "type": atype,
            "rating": info_el.select_one(".rating").get_text(strip=True) if info_el and info_el.select_one(".rating") else "",
            "mal_score": soup.select_one(".rate-box .value").get_text(strip=True) if soup.select_one(".rate-box .value") else "",
            "detail": detail,
            "seasons": seasons,
        }
    except requests.exceptions.HTTPError as he:
        if he.response.status_code == 404:
            return {"error": f"Anime '{slug}' not found on AnimeKai"}, 404
        return {"error": str(he)}, 500
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes(ani_id):
    try:
        slug = ani_id
        url = f"https://animekai.be/watch/{slug}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        episodes = []
        eplist = soup.find(class_=lambda c: c and "eplist" in c)
        if eplist:
            for ep in eplist.find_all("a"):
                num = ep.get("num", "")
                token = f"{slug}:ep-{num}"
                langs = ep.get("langs", "1")
                episodes.append({
                    "number": num,
                    "slug": f"ep-{num}",
                    "title": f"Episode {num}",
                    "japanese_title": "",
                    "token": token,
                    "has_sub": bool(int(langs) & 1) if langs.isdigit() else True,
                    "has_dub": bool(int(langs) & 2) if langs.isdigit() else False,
                })
        return episodes
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_servers(ep_token):
    try:
        if ":" not in ep_token:
            return {"error": "Invalid episode token format"}, 400
        slug, ep_num = ep_token.split(":", 1)
        url = f"https://animekai.be/watch/{slug}/{ep_num}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        servers = {}
        for group in soup.select(".server-items"):
            lang = group.get("data-id", "sub")
            servers[lang] = []
            for s in group.select(".server"):
                link_id = s.get("data-url", "")
                servers[lang].append({
                    "name": s.get_text(strip=True),
                    "server_id": s.get("data-sid", ""),
                    "episode_id": ep_num,
                    "link_id": link_id,
                })
        
        return {
            "watching": soup.select_one(".server-note p").get_text(strip=True) if soup.select_one(".server-note p") else "",
            "servers": servers
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_source(link_id):
    try:
        # Shiva Server (HAnime) fallback check in resolve_source
        if link_id.startswith("hanime:"):
            from scraper_service.sources.hanime import resolve_hanime_source
            return resolve_hanime_source(link_id)

        embed_url = link_id

        # Fix collapsed slashes in URL schemes
        if embed_url.startswith("https:/") and not embed_url.startswith("https://"):
            embed_url = embed_url.replace("https:/", "https://", 1)
        elif embed_url.startswith("http:/") and not embed_url.startswith("http://"):
            embed_url = embed_url.replace("http:/", "http://", 1)
            
        if not embed_url.startswith("http"):
            encoded = encode_token(link_id)
            if not encoded: return {"error": "Token encryption failed"}, 500
            resp = requests.get(ANIMEKAI_LINKS_VIEW_URL, params={"id": link_id, "_": encoded}, headers=AJAX_HEADERS, timeout=15)
            resp.raise_for_status()
            encrypted_result = resp.json().get("result", "")
            embed_data = decode_kai(encrypted_result)
            embed_url = embed_data.get("url", "") if embed_data else ""
        
        if not embed_url:
            return {"error": "No embed URL found"}, 400

        try:
            referer = "https://animekai.be/"
            if "aniwatch" in embed_url or "1anime" in embed_url or "megaplay.buzz" in embed_url:
                referer = "https://aniwatch.co.at/"
            headers = {**HEADERS, "Referer": referer}
            resp = requests.get(embed_url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            player_div = soup.find(id="megaplay-player")
            player_id = player_div.get("data-id") if player_div else ""
            if not player_id:
                match_id = re.search(r'data-id=["\']([0-9]+)["\']', resp.text)
                player_id = match_id.group(1) if match_id else ""
                
            inner_url = ""
            inner_soup = None
            if not player_id:
                iframe = soup.find("iframe")
                inner_url = iframe.get("src") if iframe else ""
                if not inner_url:
                    match = re.search(r'src=["\'](https://megaplay\.buzz/stream/[^"\']+)["\']', resp.text)
                    inner_url = match.group(1) if match else ""
                
                if inner_url:
                    inner_headers = {**HEADERS, "Referer": embed_url}
                    inner_resp = requests.get(inner_url, headers=inner_headers, timeout=15)
                    inner_resp.raise_for_status()
                    
                    inner_soup = BeautifulSoup(inner_resp.text, "html.parser")
                    player_div = inner_soup.find(id="megaplay-player")
                    player_id = player_div.get("data-id") if player_div else ""
                    if not player_id:
                        match_id = re.search(r'data-id=["\']([0-9]+)["\']', inner_resp.text)
                        player_id = match_id.group(1) if match_id else ""
            
            # Check for direct html5 video element if no player_id resolved
            if not player_id:
                video_el = None
                active_soup = soup
                if inner_soup:
                    video_el = inner_soup.find("video")
                    if video_el:
                        active_soup = inner_soup
                if not video_el:
                    video_el = soup.find("video")
                    if video_el:
                        active_soup = soup
                
                if video_el:
                    sources = []
                    for src_el in video_el.find_all("source"):
                        src_url = src_el.get("src")
                        if src_url:
                            if src_url.startswith("/"):
                                from urllib.parse import urljoin
                                src_url = urljoin(embed_url, src_url)
                            sources.append({
                                "file": src_url,
                                "type": src_el.get("type", "").split("/")[-1] if "/" in src_el.get("type", "") else "mp4",
                                "label": "HD"
                            })
                    if not sources and video_el.get("src"):
                        src_url = video_el.get("src")
                        if src_url.startswith("/"):
                            from urllib.parse import urljoin
                            src_url = urljoin(embed_url, src_url)
                        sources.append({
                            "file": src_url,
                            "type": "mp4",
                            "label": "HD"
                        })
                    
                    if sources:
                        tracks = []
                        for trk_el in video_el.find_all("track"):
                            trk_url = trk_el.get("src")
                            if trk_url and trk_url.startswith("/"):
                                from urllib.parse import urljoin
                                trk_url = urljoin(embed_url, trk_url)
                            tracks.append({
                                "file": trk_url,
                                "kind": trk_el.get("kind", "captions"),
                                "label": trk_el.get("label", "English"),
                                "default": trk_el.get("default") is not None
                            })
                        
                        download_url = ""
                        for a_el in active_soup.find_all("a"):
                            href = a_el.get("href", "")
                            if "download" in href.lower():
                                from urllib.parse import urljoin
                                download_url = urljoin(embed_url, href)
                                break
                                
                        return {
                            "embed_url": embed_url,
                            "skip": {},
                            "sources": sources,
                            "tracks": tracks,
                            "download": download_url
                        }
            
            if player_id:
                parsed_base = embed_url.rsplit("/stream/", 1)[0] if "/stream/" in embed_url else embed_url.rsplit("/", 1)[0]
                if inner_url and "/stream/" in inner_url:
                    parsed_base = inner_url.rsplit("/stream/", 1)[0]
                
                sources_url = f"{parsed_base}/stream/getSources?id={player_id}"
                sources_headers = {
                    **HEADERS,
                    "Referer": inner_url if inner_url else embed_url,
                    "X-Requested-With": "XMLHttpRequest"
                }
                sources_resp = requests.get(sources_url, headers=sources_headers, timeout=15)
                if sources_resp.status_code == 200:
                    get_sources_json = sources_resp.json()
                    
                    sources = []
                    raw_sources = get_sources_json.get("sources")
                    if isinstance(raw_sources, dict):
                        hls_file = raw_sources.get("file", "")
                        if hls_file:
                            sources.append({"file": hls_file, "type": "hls", "label": "Auto"})
                    elif isinstance(raw_sources, list):
                        for src in raw_sources:
                            if isinstance(src, dict):
                                sources.append({
                                    "file": src.get("file", ""),
                                    "type": src.get("type", "hls"),
                                    "label": src.get("label", "Auto")
                                })
                                
                    skip_data = {}
                    raw_intro = get_sources_json.get("intro", {})
                    raw_outro = get_sources_json.get("outro", {})
                    
                    intro_start = raw_intro.get("start", 0) if isinstance(raw_intro, dict) else 0
                    intro_end = raw_intro.get("end", 0) if isinstance(raw_intro, dict) else 0
                    outro_start = raw_outro.get("start", 0) if isinstance(raw_outro, dict) else 0
                    outro_end = raw_outro.get("end", 0) if isinstance(raw_outro, dict) else 0
                    
                    skip_data["intro"] = [intro_start, intro_end]
                    skip_data["outro"] = [outro_start, outro_end]
                    
                    return {
                        "embed_url": embed_url,
                        "skip": skip_data,
                        "sources": sources,
                        "tracks": get_sources_json.get("tracks", []),
                        "download": get_sources_json.get("download", "")
                    }
        except Exception as inner_e:
            print("Inner media resolution error:", inner_e)

        return {
            "embed_url": embed_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": "",
            "message": "Direct player fallback: iframe mode."
        }
    except Exception as e:
        return {"error": str(e)}, 500
