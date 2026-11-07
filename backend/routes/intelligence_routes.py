from fastapi import APIRouter, HTTPException
from api.schemas import IntelligenceRequest
from core.financial_state import FinancialState
from services.intelligence_service import IntelligenceService

router = APIRouter()
service = IntelligenceService()

@router.post("/api/intelligence/insights", tags=["Intelligence"])
async def get_insights(body: IntelligenceRequest):
    data = body.model_dump()

    required_fields = [
        "income", "expenses", "savings", "debt",
        "risk_score", "investment_exposure",
        "goal_horizon_months", "emergency_fund_months"
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        financial_state = FinancialState(
            income=data["income"],
            expenses=data["expenses"],
            savings=data["savings"],
            debt=data["debt"],
            risk_score=data["risk_score"],
            investment_exposure=data["investment_exposure"],
            goal_horizon_months=data["goal_horizon_months"],
            emergency_fund_months=data["emergency_fund_months"]
        )

        insights = service.run(financial_state)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to generate insights") from e

