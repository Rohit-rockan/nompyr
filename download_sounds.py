import urllib.request
import urllib.parse
import json
import os
import sys

def download_commons_audio(keyword, output_filename):
    print(f"Searching for {keyword}...")
    search_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(keyword)}&srnamespace=6&utf8=&format=json"
    
    req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    for result in data['query']['search']:
        title = result['title']
        if title.lower().endswith(('.ogg', '.mp3', '.wav', '.flac')):
            print(f"Found: {title}")
            info_url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=imageinfo&iiprop=url&format=json"
            req2 = urllib.request.Request(info_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2) as resp2:
                info_data = json.loads(resp2.read().decode())
                pages = info_data['query']['pages']
                for page_id in pages:
                    url = pages[page_id]['imageinfo'][0]['url']
                    print(f"Downloading {url} to {output_filename}")
                    
                    req_dl = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_dl) as dl_resp:
                        with open(output_filename, 'wb') as f:
                            f.write(dl_resp.read())
                    print("Success!")
                    return True
    
    print(f"Could not find a suitable audio file for {keyword}")
    return False

# Mapping
targets = {
    "Ocean waves audio": "frontend-isekai/public/audio/base_ambience.mp3",
    "Thunder rumble sound": "frontend-isekai/public/audio/rumble.mp3",
    "Chime sound": "frontend-isekai/public/audio/hover_sparkle.mp3",
    "Water drop sound": "frontend-isekai/public/audio/click_ripple.mp3",
    "Orchestra audio": "frontend-isekai/public/audio/gate_swell.mp3"
}

for kw, outfile in targets.items():
    download_commons_audio(kw, outfile)
