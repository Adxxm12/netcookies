# backend/main.py
import os
import sys
import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Tambah folder backend/ ke sys.path supaya boleh import bot
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from bot import (
    try_get_login_url,
    get_stock_by_plan,
)

# ==================== CONFIG ====================
TIMEZONE = timezone(timedelta(hours=8))  # Malaysia
DAILY_LIMIT = 1
USD_TO_MYR = 4.70
VERIFY_DELAY_SECONDS = 60          # 1 minit auto-verify
ORDER_COOLDOWN_SECONDS = 300       # 5 minit cooldown

# FIX: absolute path — elak data hilang bila Render redeploy
DATA_FILE = os.path.join(os.path.dirname(__file__), "backend_data.json")

# Ambil dari .env (JANGAN HARDCODE!)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("⚠️ WARNING: SUPABASE_URL atau SUPABASE_SERVICE_KEY tak ada dalam .env")

app = FastAPI(title="NetCookies API")

# FIX: CORS — domain kau sahaja, bukan *
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://netcookies.store",
        "https://www.netcookies.store",
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",   # fallback dev
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

security = HTTPBearer()

# ==================== SIMPLE JSON DATABASE ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"claims": {}, "quota": {}, "orders": {}}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            data.setdefault("claims", {})
            data.setdefault("quota", {})
            data.setdefault("orders", {})
            return data
    except Exception:
        return {"claims": {}, "quota": {}, "orders": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ==================== AUTH HELPER ====================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_SERVICE_KEY,
            },
            timeout=10,
        )

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return res.json()

# ==================== MODELS ====================
class ClaimRequest(BaseModel):
    product_id: int

class CheckoutItem(BaseModel):
    plan: str
    quantity: int
    price_usd: float

class CheckoutRequest(BaseModel):
    items: list[CheckoutItem]

# ==================== BASIC ENDPOINTS ====================
@app.get("/")
def root():
    return {"status": "NetCookies API running", "time": datetime.now(TIMEZONE).isoformat()}

@app.get("/api/rewards")
def get_rewards():
    return {
        "products": [
            {"id": 1, "name": "Netflix Premium", "country": "🇲🇾 Malaysia", "plan": "Premium", "quality": "4K UHD", "duration": "30 Days", "price": 0.50},
            {"id": 2, "name": "Netflix Premium", "country": "🇻🇳 Vietnam", "plan": "Premium", "quality": "4K UHD", "duration": "30 Days", "price": 0.50},
            {"id": 3, "name": "Netflix Standard", "country": "🇲🇾 Malaysia", "plan": "Standard", "quality": "1080p", "duration": "30 Days", "price": 0.25},
            {"id": 4, "name": "Netflix Premium", "country": "🇮🇩 Indonesia", "plan": "Premium", "quality": "4K UHD", "duration": "30 Days", "price": 0.50},
            {"id": 5, "name": "Netflix Premium", "country": "🇵🇭 Philippines", "plan": "Premium", "quality": "4K UHD", "duration": "30 Days", "price": 0.50},
            {"id": 6, "name": "Netflix Basic", "country": "🇲🇾 Malaysia", "plan": "Basic", "quality": "720p", "duration": "30 Days", "price": 0.25},
            {"id": 7, "name": "Netflix Basic", "country": "🇮🇩 Indonesia", "plan": "Basic", "quality": "720p", "duration": "30 Days", "price": 0.25},
        ]
    }

@app.get("/api/stock")
def get_stock():
    stock = get_stock_by_plan()
    return {"stock": stock, "total": sum(stock.values())}

# ==================== GIVEAWAY (FREE CLAIM) ====================
@app.get("/api/giveaway/quota")
async def get_quota(user = Depends(get_current_user)):
    user_id = user["id"]
    data = load_data()
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    key = f"{user_id}_{today}"
    used = data["quota"].get(key, 0)
    return {
        "remaining": max(0, DAILY_LIMIT - used),
        "total": DAILY_LIMIT,
        "used": used,
    }

@app.post("/api/giveaway/claim")
async def claim(req: ClaimRequest, user = Depends(get_current_user)):
    user_id = user["id"]
    data = load_data()
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    quota_key = f"{user_id}_{today}"

    used = data["quota"].get(quota_key, 0)
    if used >= DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Daily quota reached ({DAILY_LIMIT}/{DAILY_LIMIT}). Reset at midnight MYT.",
        )

    try:
        success, url, expires, error, filename, info = try_get_login_url(max_attempts=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot error: {str(e)}")

    if not success:
        raise HTTPException(status_code=503, detail=f"Out of stock: {error}")

    data["quota"][quota_key] = used + 1

    claim_id = str(uuid.uuid4())
    data["claims"].setdefault(user_id, []).append({
        "id": claim_id,
        "redemption_url": url,
        "claimed_at": datetime.now(TIMEZONE).isoformat(),
        "product_id": req.product_id,
        "plan": info.get("plan", "Unknown") if info else "Unknown",
    })
    save_data(data)

    return {
        "status": "success",
        "claim_id": claim_id,
        "redemption_url": url,
        "plan": info.get("plan", "Unknown") if info else "Unknown",
        "expires": expires,
        "remaining": max(0, DAILY_LIMIT - (used + 1)),
    }

@app.get("/api/giveaway/history")
async def get_history(user = Depends(get_current_user)):
    user_id = user["id"]
    data = load_data()
    claims = data["claims"].get(user_id, [])
    return {"history": claims, "total": len(claims)}

# ==================== CHECKOUT / ORDERS ====================
@app.post("/api/checkout")
async def checkout(req: CheckoutRequest, user = Depends(get_current_user)):
    user_id = user["id"]
    user_email = user.get("email", "")
    data = load_data()

    now = time.time()

    # Cooldown 5 minit
    for order in data["orders"].values():
        if order.get("user_id") == user_id:
            created = order.get("created_ts", 0)
            if now - created < ORDER_COOLDOWN_SECONDS:
                remaining = int(ORDER_COOLDOWN_SECONDS - (now - created))
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {remaining}s before placing another order."
                )

    # Satu pending order sahaja
    for order in data["orders"].values():
        if order.get("user_id") == user_id and order.get("status") == "pending":
            raise HTTPException(
                status_code=429,
                detail="You already have a pending order. Please complete it first."
            )

    total_usd = sum(item.price_usd * item.quantity for item in req.items)
    total_myr = round(total_usd * USD_TO_MYR, 2)

    order_id = f"ORD-{datetime.now(TIMEZONE).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    data["orders"][order_id] = {
        "order_id": order_id,
        "user_id": user_id,
        "user_email": user_email,
        "items": [item.dict() for item in req.items],
        "total_usd": total_usd,
        "total_myr": total_myr,
        "status": "pending",
        "created_at": datetime.now(TIMEZONE).isoformat(),
        "created_ts": now,
        "paid_at": None,
        "redemption_url": None,
        "plan_delivered": None,
    }
    save_data(data)

    return {
        "status": "success",
        "order_id": order_id,
        "total_usd": total_usd,
        "total_myr": total_myr,
        "qr_url": "/qr-gxbank.png",
        "verify_in_seconds": VERIFY_DELAY_SECONDS,
        "message": "Please scan the QR and pay. Your Netflix link will be ready in 1 minute.",
    }

@app.get("/api/orders/{order_id}/status")
async def order_status(order_id: str, user = Depends(get_current_user)):
    user_id = user["id"]
    data = load_data()

    order = data.get("orders", {}).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your order")

    if order["status"] == "pending":
        elapsed = time.time() - order.get("created_ts", 0)
        if elapsed >= VERIFY_DELAY_SECONDS:
            success, url, expires, error, filename, info = try_get_login_url(max_attempts=20)
            if success:
                order["status"] = "paid"
                order["paid_at"] = datetime.now(TIMEZONE).isoformat()
                order["redemption_url"] = url
                order["plan_delivered"] = info.get("plan", "Unknown") if info else "Unknown"
                data["orders"][order_id] = order
                save_data(data)
            else:
                order["last_error"] = error
                data["orders"][order_id] = order
                save_data(data)

    return {
        "order_id": order_id,
        "status": order["status"],
        "redemption_url": order.get("redemption_url"),
        "plan_delivered": order.get("plan_delivered"),
        "total_usd": order["total_usd"],
        "total_myr": order["total_myr"],
        "elapsed_seconds": int(time.time() - order.get("created_ts", 0)),
        "verify_in_seconds": VERIFY_DELAY_SECONDS,
        "message": order.get("last_error") or ("Your Netflix link is ready!" if order["status"] == "paid" else "Verifying payment..."),
    }

@app.get("/api/orders/my")
async def my_orders(user = Depends(get_current_user)):
    user_id = user["id"]
    data = load_data()
    orders = [
        o for o in data.get("orders", {}).values()
        if o["user_id"] == user_id
    ]
    orders.sort(key=lambda x: x.get("created_ts", 0), reverse=True)
    return {"orders": orders, "total": len(orders)}

# ==================== ADMIN ====================
@app.get("/api/admin/stats")
async def admin_stats(user = Depends(get_current_user)):
    data = load_data()
    orders = list(data.get("orders", {}).values())

    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    month = datetime.now(TIMEZONE).strftime("%Y-%m")

    paid_orders = [o for o in orders if o.get("status") == "paid"]

    revenue_today = sum(o["total_usd"] for o in paid_orders if (o.get("paid_at") or "").startswith(today))
    revenue_month = sum(o["total_usd"] for o in paid_orders if (o.get("paid_at") or "").startswith(month))
    revenue_total = sum(o["total_usd"] for o in paid_orders)

    plan_count = {}
    for o in paid_orders:
        for item in o.get("items", []):
            plan = item["plan"]
            plan_count[plan] = plan_count.get(plan, 0) + item["quantity"]

    return {
        "total_orders": len(orders),
        "paid_orders": len(paid_orders),
        "pending_orders": len([o for o in orders if o.get("status") == "pending"]),
        "revenue_today_usd": round(revenue_today, 2),
        "revenue_month_usd": round(revenue_month, 2),
        "revenue_total_usd": round(revenue_total, 2),
        "revenue_today_myr": round(revenue_today * USD_TO_MYR, 2),
        "revenue_month_myr": round(revenue_month * USD_TO_MYR, 2),
        "revenue_total_myr": round(revenue_total * USD_TO_MYR, 2),
        "plan_popularity": plan_count,
    }

@app.get("/api/admin/orders")
async def admin_orders(user = Depends(get_current_user)):
    data = load_data()
    orders = list(data.get("orders", {}).values())
    orders.sort(key=lambda x: x.get("created_ts", 0), reverse=True)
    return {"orders": orders, "total": len(orders)}

@app.post("/api/admin/revoke/{order_id}")
async def admin_revoke(order_id: str, user = Depends(get_current_user)):
    data = load_data()
    order = data.get("orders", {}).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order["status"] = "revoked"
    order["redemption_url"] = None
    data["orders"][order_id] = order
    save_data(data)
    return {"status": "revoked", "order_id": order_id}

# ==================== MAIN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)