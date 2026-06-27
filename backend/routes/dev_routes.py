"""FastAPI dev/test routes and intelligence insights."""

from fastapi import APIRouter, HTTPException, Path as FPath

from api.schemas import IntelligenceRequest
from db import collection

router = APIRouter()


@router.post("/api/init-test-data/{email}", tags=["Dev"])
async def init_test_data(email: str = FPath(...)):
    user = collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")

    sample = {
        "financials": {
            "monthly-income": 75000,
            "monthly-expenses": 45000,
            "debt": 150000,
            "em-fund-opted": True,
        },
        "Goal": {
            "goal": "Early Retirement",
            "target-amt": 5000000,
            "target-time": 120,
            "risk": "moderate",
        },
        "investments": {
            "risk-opt": "moderate",
            "prefered-mode": "Monthly SIP",
            "invest-amt": 15000,
        },
        "Age": "32",
        "employment-status": "Salaried",
    }
    collection.update_one({"email": email}, {"$set": sample})
    updated = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    return {"status": "success", "user": updated}


@router.post("/api/intelligence/insights", tags=["Intelligence"])
async def intelligence_insights(body: IntelligenceRequest):
    from core.financial_state import FinancialState
    from services.intelligence_service import IntelligenceService

    try:
        state = FinancialState(**body.model_dump())
        return {"insights": IntelligenceService().run(state)}
    except Exception as e:
        raise HTTPException(500, str(e))
