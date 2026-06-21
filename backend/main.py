"""
Finance Tracker API — FastAPI + Supabase
"""
import os
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

app = FastAPI(title="Finance Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://zync-finance-tracker.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client — initialised once at startup
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


# ── Pydantic models ──────────────────────────────────────────

class EarningIn(BaseModel):
    amount: float
    source: str
    date: date


class SubscriptionIn(BaseModel):
    name: str
    amount: float
    date_started: date


class SpendingIn(BaseModel):
    description: str
    amount: float
    date: date


# ── Earnings ─────────────────────────────────────────────────

@app.get("/api/earnings")
def get_earnings():
    res = supabase.table("earnings").select("*").order("date", desc=True).execute()
    return res.data


@app.post("/api/earnings", status_code=201)
def create_earning(body: EarningIn):
    res = supabase.table("earnings").insert({
        "amount": body.amount,
        "source": body.source,
        "date":   str(body.date),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/earnings/{id}")
def update_earning(id: str, body: EarningIn):
    res = supabase.table("earnings").update({
        "amount": body.amount,
        "source": body.source,
        "date":   str(body.date),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Earning not found")
    return res.data[0]


@app.delete("/api/earnings/{id}", status_code=204)
def delete_earning(id: str):
    res = supabase.table("earnings").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Earning not found")


# ── Subscriptions ─────────────────────────────────────────────

@app.get("/api/subscriptions")
def get_subscriptions():
    res = supabase.table("subscriptions").select("*").order("date_started", desc=True).execute()
    return res.data


@app.post("/api/subscriptions", status_code=201)
def create_subscription(body: SubscriptionIn):
    res = supabase.table("subscriptions").insert({
        "name":         body.name,
        "amount":       body.amount,
        "date_started": str(body.date_started),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/subscriptions/{id}")
def update_subscription(id: str, body: SubscriptionIn):
    res = supabase.table("subscriptions").update({
        "name":         body.name,
        "amount":       body.amount,
        "date_started": str(body.date_started),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return res.data[0]


@app.delete("/api/subscriptions/{id}", status_code=204)
def delete_subscription(id: str):
    res = supabase.table("subscriptions").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")


# ── Spending ──────────────────────────────────────────────────

@app.get("/api/spending")
def get_spending():
    res = supabase.table("spending").select("*").order("date", desc=True).execute()
    return res.data


@app.post("/api/spending", status_code=201)
def create_spending(body: SpendingIn):
    res = supabase.table("spending").insert({
        "description": body.description,
        "amount":      body.amount,
        "date":        str(body.date),
    }).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    return res.data[0]


@app.put("/api/spending/{id}")
def update_spending(id: str, body: SpendingIn):
    res = supabase.table("spending").update({
        "description": body.description,
        "amount":      body.amount,
        "date":        str(body.date),
    }).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Spending not found")
    return res.data[0]


@app.delete("/api/spending/{id}", status_code=204)
def delete_spending(id: str):
    res = supabase.table("spending").delete().eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Spending not found")


# ── Summary ───────────────────────────────────────────────────

@app.get("/api/summary")
def get_summary():
    e  = supabase.table("earnings").select("amount").execute()
    s  = supabase.table("subscriptions").select("amount").execute()
    sp = supabase.table("spending").select("amount").execute()

    total_earnings      = sum(float(r["amount"]) for r in e.data)
    total_subscriptions = sum(float(r["amount"]) for r in s.data)
    total_spending      = sum(float(r["amount"]) for r in sp.data)

    return {
        "total_earnings":      total_earnings,
        "total_subscriptions": total_subscriptions,
        "total_spending":      total_spending,
        "net":                 total_earnings - total_subscriptions - total_spending,
    }
