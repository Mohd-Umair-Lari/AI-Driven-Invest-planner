"""FastAPI user routes: get and update user profile."""

from fastapi import APIRouter, HTTPException, Path as FPath

from api.schemas import UserUpdateRequest
from db import collection, trigger_user_indexing

router = APIRouter(tags=["User"])


@router.get("/api/user/{email}")
async def get_user(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return {"status": "success", "user": user}


@router.put("/api/user/{email}")
async def update_user(body: UserUpdateRequest, email: str = FPath(...)):
    user = collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")

    existing_financials = user.get("financials", {})
    existing_investments = user.get("investments", {})
    existing_progress = user.get("progress", {})

    updated_financials = {**existing_financials, **(body.financials or {})}
    updated_investments = {**existing_investments, **(body.investments or {})}
    updated_progress = {**existing_progress, **(body.progress or {})}

    result = collection.update_one(
        {"email": email},
        {
            "$set": {
                "Name": body.Name,
                "Age": str(body.Age or ""),
                "employment-status": body.employment_status or "",
                "Goal": body.Goal or {},
                "financials": updated_financials,
                "investments": updated_investments,
                "progress": updated_progress,
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")

    trigger_user_indexing(email)

    return {"status": "success"}
