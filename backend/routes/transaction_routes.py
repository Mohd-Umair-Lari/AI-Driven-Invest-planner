"""FastAPI transaction routes."""

from fastapi import APIRouter, HTTPException, Path as FPath

from db import collection

router = APIRouter(tags=["Transactions"])


@router.post("/api/transactions/{email}", status_code=201)
async def add_transactions(email: str = FPath(...), transactions: list = None):
    if not transactions:
        raise HTTPException(400, "No transactions provided")
    result = collection.update_one(
        {"email": email},
        {"$push": {"transactions": {"$each": transactions}}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"status": "success", "added": len(transactions)}


@router.get("/api/transactions/{email}")
async def get_transactions(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "transactions": 1})
    if not user:
        raise HTTPException(404, "User not found")
    return {"transactions": user.get("transactions", [])}
