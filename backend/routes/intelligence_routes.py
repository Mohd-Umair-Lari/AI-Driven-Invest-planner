from flask import Blueprint, request, jsonify
from ..core.financial_state import FinancialState
from ..services.intelligence_service import IntelligenceService

intelligence_bp = Blueprint("intelligence", __name__)
service = IntelligenceService()


@intelligence_bp.route("/intelligence/insights", methods=["POST"])
def get_insights():
    data = request.json

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

    return jsonify({"insights": insights})
