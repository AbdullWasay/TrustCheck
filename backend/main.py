import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from supabase import Client, create_client

from trust_engine import assess_seller

PK_PHONE_PATTERN = re.compile(r"^(?:\+92|0092|0)?3\d{2}[-\s]?\d{7}$")

# Load backend/.env then repo-root .env (local + Vercel-compatible)
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app = FastAPI(title="TrustCheck PK API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or ""
    ).strip()

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY. "
                "Set them in Vercel Project Settings → Environment Variables."
            ),
        )

    return create_client(supabase_url, supabase_key)


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        name = value.strip()
        if not name:
            return None
        if len(name) < 2:
            raise ValueError("Enter a valid name.")
        return name


class SellerStartRequest(BaseModel):
    website: str
    phone: str
    seller_type: str

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str) -> str:
        website = value.strip()
        if not website:
            raise ValueError("Website or social profile is required.")

        candidate = website if re.match(r"^https?://", website, re.I) else f"https://{website}"
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or "." not in (parsed.hostname or ""):
            raise ValueError("Enter a valid website or profile URL.")
        return candidate

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        phone = value.strip()
        compact = re.sub(r"[()\s]", "", phone)
        if not PK_PHONE_PATTERN.match(compact):
            raise ValueError(
                "Enter a valid Pakistan mobile number (e.g. 0300-1234567)."
            )
        return phone


class SellerDetailsRequest(BaseModel):
    seller_name: str
    payment_method: str
    return_policy: str

    @field_validator("seller_name")
    @classmethod
    def validate_seller_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("Seller name looks too short.")
        if len(name) > 80:
            raise ValueError("Seller name is too long.")
        return name



def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_or_401(x_user_id: Optional[str]) -> dict[str, Any]:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing user session.")

    supabase = get_supabase()
    response = (
        supabase.table("app_users")
        .select("id,email,full_name,created_at")
        .eq("id", x_user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid user session.")

    return response.data[0]


def serialize_check(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "user_id": row.get("user_id"),
        "website": row.get("website"),
        "phone": row.get("phone"),
        "seller_type": row.get("seller_type"),
        "seller_name": row.get("seller_name"),
        "payment_method": row.get("payment_method"),
        "return_policy": row.get("return_policy"),
        "risk_level": row.get("risk_level"),
        "decision": row.get("decision"),
        "positive_signals": row.get("positive_signals") or [],
        "warning_signals": row.get("warning_signals") or [],
        "checklist": row.get("checklist") or [],
        "summary": row.get("summary"),
        "status": row.get("status"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "TrustCheck PK API"}


@app.post("/api/auth/register")
def register(payload: AuthRequest) -> dict[str, Any]:
    email = payload.email.lower().strip()
    supabase = get_supabase()

    existing = (
        supabase.table("app_users")
        .select("id")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    try:
        inserted = (
            supabase.table("app_users")
            .insert(
                {
                    "email": email,
                    "password_hash": hash_password(payload.password),
                    "full_name": payload.full_name or email.split("@")[0],
                }
            )
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create user in Supabase. "
                "Make sure supabase/schema.sql has been run. "
                f"Details: {exc}"
            ),
        ) from exc

    if not inserted.data:
        raise HTTPException(status_code=500, detail="User was not created.")

    user = inserted.data[0]
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
        }
    }


@app.post("/api/auth/login")
def login(payload: AuthRequest) -> dict[str, Any]:
    email = payload.email.lower().strip()
    supabase = get_supabase()

    response = (
        supabase.table("app_users")
        .select("id,email,full_name,password_hash")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = response.data[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
        }
    }


@app.get("/api/me")
def me(x_user_id: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    return {"user": user}


@app.get("/api/checks")
def list_checks(x_user_id: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    supabase = get_supabase()
    response = (
        supabase.table("seller_checks")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"checks": [serialize_check(row) for row in (response.data or [])]}


@app.post("/api/checks")
def start_check(
    payload: SellerStartRequest,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    supabase = get_supabase()

    inserted = (
        supabase.table("seller_checks")
        .insert(
            {
                "user_id": user["id"],
                "website": payload.website.strip(),
                "phone": payload.phone.strip(),
                "seller_type": payload.seller_type,
                "status": "draft",
                "updated_at": now_iso(),
            }
        )
        .execute()
    )

    if not inserted.data:
        raise HTTPException(status_code=500, detail="Could not save seller check.")

    return {"check": serialize_check(inserted.data[0])}


@app.put("/api/checks/{check_id}/details")
def update_details(
    check_id: str,
    payload: SellerDetailsRequest,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    supabase = get_supabase()

    existing = (
        supabase.table("seller_checks")
        .select("*")
        .eq("id", check_id)
        .eq("user_id", user["id"])
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Seller check not found.")

    current = existing.data[0]
    assessment = assess_seller(
        {
            "website": current.get("website"),
            "phone": current.get("phone"),
            "seller_type": current.get("seller_type"),
            "seller_name": payload.seller_name,
            "payment_method": payload.payment_method,
            "return_policy": payload.return_policy,
        }
    )

    updated = (
        supabase.table("seller_checks")
        .update(
            {
                "seller_name": payload.seller_name.strip(),
                "payment_method": payload.payment_method,
                "return_policy": payload.return_policy,
                "risk_level": assessment["risk_level"],
                "decision": assessment["decision"],
                "positive_signals": assessment["positive_signals"],
                "warning_signals": assessment["warning_signals"],
                "checklist": assessment["checklist"],
                "summary": assessment["summary"],
                "status": "completed",
                "updated_at": now_iso(),
            }
        )
        .eq("id", check_id)
        .eq("user_id", user["id"])
        .execute()
    )

    if not updated.data:
        raise HTTPException(status_code=500, detail="Could not update seller check.")

    return {"check": serialize_check(updated.data[0])}


@app.get("/api/checks/{check_id}")
def get_check(
    check_id: str,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    supabase = get_supabase()
    response = (
        supabase.table("seller_checks")
        .select("*")
        .eq("id", check_id)
        .eq("user_id", user["id"])
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Seller check not found.")

    return {"check": serialize_check(response.data[0])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
