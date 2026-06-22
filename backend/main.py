"""
Finance Tracker API — FastAPI + Supabase

Multi-user: authentication is handled by Supabase Auth (bcrypt + JWT) and
proxied through this API so we control rate limiting and keep all Supabase keys
server-side. Per-user data isolation is enforced by Postgres Row-Level Security
(see migrations/001_auth_rls.sql) — every data request runs under the caller's
JWT, so the database itself guarantees a user only ever touches their own rows.
"""
import os
from datetime import date

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]   # anon (public) key

# Supabase signs access tokens with asymmetric keys (ES256). We verify them
# against the project's public JWKS endpoint — no shared secret needed. Keys are
# fetched once and cached.
_jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True)

app = FastAPI(title="Finance Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://zync-finance-tracker.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate limiting ─────────────────────────────────────────────
# Behind Vercel/host proxies the real client IP is in X-Forwarded-For; fall back
# to the socket address for local/dev. In-memory store is per-instance (fine for
# a single backend instance — see plan caveats for horizontal scaling).
def _rate_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else get_remote_address(request)


limiter = Limiter(key_func=_rate_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Anon client — used for the auth flows (sign-up / sign-in / refresh).
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Auth dependencies ─────────────────────────────────────────

def _bearer_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization[7:]


def get_current_user(token: str = Depends(_bearer_token)) -> dict:
    """Verify the Supabase access token (signature via JWKS, audience, expiry)."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated"
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"id": claims["sub"], "token": token}


def get_db(user: dict = Depends(get_current_user)) -> Client:
    """Per-request Supabase client authed as the caller so RLS scopes queries."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.postgrest.auth(user["token"])
    return client


# ── Auth models ───────────────────────────────────────────────

class RegisterIn(BaseModel):
    email:    EmailStr
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email:    EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


# ── Data models ───────────────────────────────────────────────
# Length caps are defense-in-depth input limits (also blunt abusive payloads).

class EarningIn(BaseModel):
    amount: float
    source: str = Field(min_length=1, max_length=200)
    date:   date


class SubscriptionIn(BaseModel):
    name:         str = Field(min_length=1, max_length=200)
    amount:       float
    date_started: date


class SpendingIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount:      float
    date:        date


# ── Auth endpoints ────────────────────────────────────────────

@app.post("/api/auth/register", status_code=201)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterIn):
    try:
        res = supabase.auth.sign_up({
            "email":    body.email,
            "password": body.password,
            "options":  {"data": {"username": body.username}},
        })
    except Exception:
        # Generic message — do not leak whether the email already exists.
        raise HTTPException(status_code=400, detail="Could not complete registration")

    if res.user is None:
        raise HTTPException(status_code=400, detail="Could not complete registration")

    # Pre-insert the profile using the service-role key so it exists the moment
    # the user confirms their email (the RLS authed path isn't available yet).
    try:
        svc_key = os.environ.get("SUPABASE_SERVICE_KEY")
        if svc_key:
            svc = create_client(SUPABASE_URL, svc_key)
            svc.table("profiles").upsert({"id": res.user.id, "username": body.username}).execute()
    except Exception:
        raise HTTPException(status_code=409, detail="Username is already taken")

    # Email confirmation is required — no session yet.
    if res.session is None:
        return {"needs_confirmation": True}

    return {
        "access_token":  res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "user": {"id": res.user.id, "email": res.user.email, "username": body.username},
    }


@app.post("/api/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginIn):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": body.email, "password": body.password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if res.session is None or res.user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "access_token":  res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "user": {
            "id":       res.user.id,
            "email":    res.user.email,
            "username": (res.user.user_metadata or {}).get("username"),
        },
    }


@app.post("/api/auth/refresh")
@limiter.limit("30/minute")
def refresh(request: Request, body: RefreshIn):
    try:
        res = supabase.auth.refresh_session(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if res.session is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return {
        "access_token":  res.session.access_token,
        "refresh_token": res.session.refresh_token,
    }


# ── Earnings ─────────────────────────────────────────────────

@app.get("/api/earnings")
def get_earnings(db: Client = Depends(get_db)):
    res = db.table("earnings").select("*").order("date", desc=True).execute()
    return res.data


@app.post("/api/earnings", status_code=201)
def create_earning(body: EarningIn, db: Client = Depends(get_db)):
    res = db.table("earnings").insert({
        "amount": body.amount,
        "source": body.source,
        "date":   str(body.date),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/earnings/{id}")
def update_earning(id: str, body: EarningIn, db: Client = Depends(get_db)):
    res = db.table("earnings").update({
        "amount": body.amount,
        "source": body.source,
        "date":   str(body.date),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Earning not found")
    return res.data[0]


@app.delete("/api/earnings/{id}", status_code=204)
def delete_earning(id: str, db: Client = Depends(get_db)):
    res = db.table("earnings").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Earning not found")


# ── Subscriptions ─────────────────────────────────────────────

@app.get("/api/subscriptions")
def get_subscriptions(db: Client = Depends(get_db)):
    res = db.table("subscriptions").select("*").order("date_started", desc=True).execute()
    return res.data


@app.post("/api/subscriptions", status_code=201)
def create_subscription(body: SubscriptionIn, db: Client = Depends(get_db)):
    res = db.table("subscriptions").insert({
        "name":         body.name,
        "amount":       body.amount,
        "date_started": str(body.date_started),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/subscriptions/{id}")
def update_subscription(id: str, body: SubscriptionIn, db: Client = Depends(get_db)):
    res = db.table("subscriptions").update({
        "name":         body.name,
        "amount":       body.amount,
        "date_started": str(body.date_started),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return res.data[0]


@app.delete("/api/subscriptions/{id}", status_code=204)
def delete_subscription(id: str, db: Client = Depends(get_db)):
    res = db.table("subscriptions").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")


# ── Spending ──────────────────────────────────────────────────

@app.get("/api/spending")
def get_spending(db: Client = Depends(get_db)):
    res = db.table("spending").select("*").order("date", desc=True).execute()
    return res.data


@app.post("/api/spending", status_code=201)
def create_spending(body: SpendingIn, db: Client = Depends(get_db)):
    res = db.table("spending").insert({
        "description": body.description,
        "amount":      body.amount,
        "date":        str(body.date),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/spending/{id}")
def update_spending(id: str, body: SpendingIn, db: Client = Depends(get_db)):
    res = db.table("spending").update({
        "description": body.description,
        "amount":      body.amount,
        "date":        str(body.date),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Spending not found")
    return res.data[0]


@app.delete("/api/spending/{id}", status_code=204)
def delete_spending(id: str, db: Client = Depends(get_db)):
    res = db.table("spending").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Spending not found")


# ── Summary ───────────────────────────────────────────────────

@app.get("/api/summary")
def get_summary(db: Client = Depends(get_db)):
    e  = db.table("earnings").select("amount").execute()
    s  = db.table("subscriptions").select("amount").execute()
    sp = db.table("spending").select("amount").execute()

    total_earnings      = sum(float(r["amount"]) for r in e.data)
    total_subscriptions = sum(float(r["amount"]) for r in s.data)
    total_spending      = sum(float(r["amount"]) for r in sp.data)

    return {
        "total_earnings":      total_earnings,
        "total_subscriptions": total_subscriptions,
        "total_spending":      total_spending,
        "net":                 total_earnings - total_subscriptions - total_spending,
    }
