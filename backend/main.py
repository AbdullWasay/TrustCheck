import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator

from supabase_rest import SupabaseRestError, get_rest_client
from trust_engine import assess_seller

_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")

PK_PHONE_PATTERN = re.compile(r"^(?:\+92|0092|0)?3\d{2}[-\s]?\d{7}$")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app = FastAPI(title="TrustCheck PK API", version="1.0.0")
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in cors_origins else cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

        candidate = (
            website if re.match(r"^https?://", website, re.I) else f"https://{website}"
        )
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or "." not in (parsed.hostname or ""):
            raise ValueError("Enter a valid website or profile URL.")
        return candidate

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        phone = value.trim()
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
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        120_000,
    ).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    # New format used by this app on Vercel
    if password_hash.startswith("pbkdf2$"):
        try:
            _, salt, expected = password_hash.split("$", 2)
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt),
                120_000,
            ).hex()
            return hmac.compare_digest(actual, expected)
        except ValueError:
            return False

    # Legacy bcrypt hashes from earlier local builds (optional)
    if password_hash.startswith("$2"):
        try:
            import bcrypt  # type: ignore

            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception:  # noqa: BLE001
            return False

    return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    try:
        return get_rest_client()
    except SupabaseRestError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_user_or_401(x_user_id: Optional[str]) -> dict[str, Any]:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing user session.")

    rows = db().select(
        "app_users",
        columns="id,email,full_name,created_at",
        filters={"id": f"eq.{x_user_id}"},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid user session.")
    return rows[0]


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


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "TrustCheck PK API"}


@router.post("/auth/register")
def register(payload: AuthRequest) -> dict[str, Any]:
    email = payload.email.lower().strip()
    client = db()

    existing = client.select(
        "app_users",
        columns="id",
        filters={"email": f"eq.{email}"},
        limit=1,
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    try:
        inserted = client.insert(
            "app_users",
            {
                "email": email,
                "password_hash": hash_password(payload.password),
                "full_name": payload.full_name or email.split("@")[0],
            },
        )
    except SupabaseRestError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create user in Supabase. "
                "Check env vars and schema. "
                f"Details: {exc}"
            ),
        ) from exc

    if not inserted:
        raise HTTPException(status_code=500, detail="User was not created.")

    user = inserted[0]
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
        }
    }


@router.post("/auth/login")
def login(payload: AuthRequest) -> dict[str, Any]:
    email = payload.email.lower().strip()
    rows = db().select(
        "app_users",
        columns="id,email,full_name,password_hash",
        filters={"email": f"eq.{email}"},
        limit=1,
    )

    if not rows:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = rows[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
        }
    }


@router.get("/me")
def me(x_user_id: Optional[str] = Header(default=None)) -> dict[str, Any]:
    return {"user": get_user_or_401(x_user_id)}


@router.get("/checks")
def list_checks(x_user_id: Optional[str] = Header(default=None)) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    rows = db().select(
        "seller_checks",
        columns="*",
        filters={"user_id": f"eq.{user['id']}"},
        order="created_at.desc",
    )
    return {"checks": [serialize_check(row) for row in rows]}


@router.post("/checks")
def start_check(
    payload: SellerStartRequest,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    try:
        inserted = db().insert(
            "seller_checks",
            {
                "user_id": user["id"],
                "website": payload.website.strip(),
                "phone": payload.phone.strip(),
                "seller_type": payload.seller_type,
                "status": "draft",
                "updated_at": now_iso(),
            },
        )
    except SupabaseRestError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not inserted:
        raise HTTPException(status_code=500, detail="Could not save seller check.")

    return {"check": serialize_check(inserted[0])}


@router.put("/checks/{check_id}/details")
def update_details(
    check_id: str,
    payload: SellerDetailsRequest,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    client = db()

    existing = client.select(
        "seller_checks",
        columns="*",
        filters={"id": f"eq.{check_id}", "user_id": f"eq.{user['id']}"},
        limit=1,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Seller check not found.")

    current = existing[0]
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

    try:
        updated = client.update(
            "seller_checks",
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
            },
            filters={"id": f"eq.{check_id}", "user_id": f"eq.{user['id']}"},
        )
    except SupabaseRestError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=500, detail="Could not update seller check.")

    return {"check": serialize_check(updated[0])}


@router.get("/checks/{check_id}")
def get_check(
    check_id: str,
    x_user_id: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    user = get_user_or_401(x_user_id)
    rows = db().select(
        "seller_checks",
        columns="*",
        filters={"id": f"eq.{check_id}", "user_id": f"eq.{user['id']}"},
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Seller check not found.")
    return {"check": serialize_check(rows[0])}


# Mount under /api (public URL) and also at root (in case Vercel strips /api)
app.include_router(router, prefix="/api")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
