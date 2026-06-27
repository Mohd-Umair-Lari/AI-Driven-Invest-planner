"""FastAPI onboarding routes: start, save, cancel, complete, status."""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path as FPath

from api.schemas import (
    OnboardingCancelRequest,
    OnboardingCompleteRequest,
    OnboardingSaveRequest,
    OnboardingStartRequest,
)
from db import collection, ensure_onboarding

router = APIRouter(tags=["Onboarding"])


@router.post("/api/onboarding/start")
async def onboarding_start(body: OnboardingStartRequest):
    user = collection.find_one({"email": body.email})
    if not user:
        raise HTTPException(404, "User not found")

    user = ensure_onboarding(body.email, user)

    if user["onboarding"]["status"] in ("not_started", "cancelled"):
        ob = {
            "status": "in_progress",
            "current_step": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }
        collection.update_one({"email": body.email}, {"$set": {"onboarding": ob}})
        user["onboarding"] = ob

    return {"status": "success", "onboarding": user["onboarding"]}


@router.post("/api/onboarding/save")
async def onboarding_save(body: OnboardingSaveRequest):
    user = collection.find_one({"email": body.email})
    if not user:
        raise HTTPException(404, "User not found")

    merged = {**user.get("onboarding", {}).get("data", {}), **body.payload}
    collection.update_one(
        {"email": body.email},
        {
            "$set": {
                "onboarding.status": "in_progress",
                "onboarding.current_step": body.step,
                "onboarding.data": merged,
                "onboarding.last_updated": datetime.utcnow().isoformat(),
            }
        },
    )
    return {"status": "saved"}


@router.post("/api/onboarding/cancel")
async def onboarding_cancel(body: OnboardingCancelRequest):
    upd: Dict[str, Any] = {
        "onboarding.status": "cancelled",
        "onboarding.last_updated": datetime.utcnow().isoformat(),
    }
    if body.current_step is not None:
        upd["onboarding.current_step"] = body.current_step

    collection.update_one({"email": body.email}, {"$set": upd})
    return {"status": "cancelled"}


@router.post("/api/onboarding/complete")
async def onboarding_complete(body: OnboardingCompleteRequest):
    user = collection.find_one({"email": body.email})
    if not user:
        raise HTTPException(404, "User not found")

    ob_data = user.get("onboarding", {}).get("data", {})

    update_fields = {
        "onboarding.status": "completed",
        "onboarding.current_step": None,
        "onboarding.last_updated": datetime.utcnow().isoformat(),
        "onboarding.data": ob_data,
    }

    if ob_data.get("name"):
        update_fields["Name"] = ob_data["name"]
    if ob_data.get("age"):
        update_fields["Age"] = str(ob_data["age"])
    if ob_data.get("employment_status"):
        update_fields["employment-status"] = ob_data["employment_status"]

    if ob_data.get("monthly_income") or ob_data.get("monthly-income"):
        income = ob_data.get("monthly_income") or ob_data.get("monthly-income")
        if "financials" not in update_fields:
            update_fields["financials"] = user.get("financials", {})
        update_fields["financials"]["monthly-income"] = income

    if ob_data.get("monthly_expenses") or ob_data.get("monthly-expenses"):
        expenses = ob_data.get("monthly_expenses") or ob_data.get("monthly-expenses")
        if "financials" not in update_fields:
            update_fields["financials"] = user.get("financials", {})
        update_fields["financials"]["monthly-expenses"] = expenses

    collection.update_one({"email": body.email}, {"$set": update_fields})
    return {"status": "completed"}


@router.get("/api/onboarding/status/{email}")
async def onboarding_status(email: str = FPath(...)):
    user = collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")

    ob = user.get("onboarding", {})
    return {
        "status": "success",
        "onboarding": {
            "state": ob.get("status"),
            "current_step": ob.get("current_step"),
            "data": ob.get("data", {}),
        },
    }
