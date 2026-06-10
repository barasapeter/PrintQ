from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.api.deps import get_db_session
from app.db.models import Customer
from app.core.utils import process_phone

from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()

OTP_LENGTH = 6
OTP_TTL_MINUTES = 3
RESEND_COOLDOWN_MINUTES = 5
MAX_VERIFY_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_otp() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])


def _otp_payload(code: str) -> dict:
    now = _now()
    return {
        "code": code,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=OTP_TTL_MINUTES)).isoformat(),
        "attempts": 0,
        "verified": False,
    }


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class SendRequest(BaseModel):
    phone: str | None = None


class VerifyRequest(BaseModel):
    phone: str | None = None
    code: str | None = None


@router.post("/send")
async def send_otp(
    payload: SendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    if not payload.phone:
        return JSONResponse(
            status_code=400, content={"detail": "Phone number is missing"}
        )

    phone = process_phone(payload.phone)
    if phone is None:
        return JSONResponse(
            status_code=400, content={"detail": "Please provide a valid phone number"}
        )

    stmt = select(Customer).where(Customer.properties["phone"].astext == phone)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        customer = Customer(properties={"phone": phone})
        db.add(customer)
        await db.flush()

    print(customer.properties)

    existing_otp: dict | None = (customer.properties or {}).get("otp")

    if existing_otp:
        if existing_otp["verified"]:
            return JSONResponse(
                status_code=409,
                content={"detail": f"Account was already verified", "redirect": True},
            )

        created_at = _parse_dt(existing_otp["created_at"])
        cooldown_ends = created_at + timedelta(minutes=RESEND_COOLDOWN_MINUTES)

        if _now() < cooldown_ends:
            wait_seconds = int((cooldown_ends - _now()).total_seconds())
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Please wait {wait_seconds} seconds before requesting a new OTP."
                    ),
                },
            )

    code = _generate_otp()

    updated_properties = {**(customer.properties or {}), "otp": _otp_payload(code)}
    customer.properties = updated_properties

    await db.commit()
    await db.refresh(customer)

    await _dispatch_otp(phone, code)

    return JSONResponse(
        status_code=200,
        content={
            "detail": f"OTP sent to {phone}.",
            "customer": str(customer.uuid),
            "expires_in_minutes": OTP_TTL_MINUTES,
        },
    )


@router.post("/verify")
async def verify_otp(
    payload: VerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    if not payload.phone or not payload.code:
        return JSONResponse(
            status_code=400,
            content={"detail": "Phone number and OTP code are required"},
        )

    phone = process_phone(payload.phone)
    if phone is None:
        return JSONResponse(
            status_code=400, content={"detail": "Please provide a valid phone number"}
        )

    stmt = select(Customer).where(Customer.properties["phone"].astext == phone)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        return JSONResponse(status_code=404, content={"detail": "Customer not found"})

    stored_otp: dict | None = (customer.properties or {}).get("otp")

    if not stored_otp:
        return JSONResponse(
            status_code=400, content={"detail": "No OTP has been requested"}
        )

    if stored_otp.get("verified"):
        return JSONResponse(
            status_code=400, content={"detail": "OTP has already been used"}
        )

    expires_at = _parse_dt(stored_otp["expires_at"])
    if _now() > expires_at:
        return JSONResponse(
            status_code=400,
            content={"detail": "OTP has expired. Please request a new one."},
        )

    attempts: int = stored_otp.get("attempts", 0)
    if attempts >= MAX_VERIFY_ATTEMPTS:
        return JSONResponse(
            status_code=400,
            content={"detail": "Too many failed attempts. Please request a new OTP."},
        )

    if not secrets.compare_digest(stored_otp["code"], payload.code.strip()):
        stored_otp["attempts"] = attempts + 1
        customer.properties = {**customer.properties, "otp": stored_otp}
        flag_modified(customer, "properties")
        await db.commit()

        remaining = MAX_VERIFY_ATTEMPTS - stored_otp["attempts"]
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Invalid OTP. You have {max(remaining, 0)} attempts remaining",
            },
        )
    
    # # i have a weird attachment to this code block so i wont delete 😭
    # stored_otp["verified"] = True
    # stored_otp["verified_at"] = _now().isoformat()
    # customer.properties = {**customer.properties, "otp": stored_otp}

    customer.properties.pop("otp", None)
    flag_modified(customer, "properties")
    await db.commit()
    await db.refresh(customer)

    request.session["customer"] = str(customer.uuid) # we just need this. this is the point of sending an otp

    return JSONResponse(
        status_code=200,
        content={
            "detail": "OTP verified successfully.",
        },
    )


async def _dispatch_otp(phone: str, code: str) -> None:
    print(f"[OTP] {phone} → {code}")
