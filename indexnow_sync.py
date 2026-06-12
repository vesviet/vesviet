import os
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET

HOST = "tanhdev.com"
KEY = "3a9c7b2e1f48d65a90b4c2e8f1d3a5b7"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP_PATH = "public/sitemap.xml"

def get_urls_from_sitemap(sitemap_path):
    if not os.path.exists(sitemap_path):
        print(f"Error: {sitemap_path} not found.")
        sys.exit(1)
    
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    
    # XML namespace for sitemap
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    urls = []
    for loc in root.findall('.//ns:loc', namespace):
        if loc.text:
            urls.append(loc.text.strip())
            
    return urls

def ping_indexnow(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=data)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            print(f"IndexNow API response: {status}")
            if status == 200:
                print(f"Successfully submitted {len(urls)} URLs to IndexNow.")
            elif status == 202:
                print(f"Accepted {len(urls)} URLs to IndexNow (key validation pending).")
            else:
                print(f"Unexpected status: {status}")
    except urllib.error.URLError as e:
        if hasattr(e, 'code'):
            print(f"IndexNow API returned error code: {e.code} ({e.reason})")
        else:
            print(f"Error pinging IndexNow: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    print(f"Extracting URLs from {SITEMAP_PATH}...")
    urls = get_urls_from_sitemap(SITEMAP_PATH)
    if urls:
        print(f"Found {len(urls)} URLs. Sending to IndexNow...")
        ping_indexnow(urls)
    else:
        print("No URLs found in sitemap.")
