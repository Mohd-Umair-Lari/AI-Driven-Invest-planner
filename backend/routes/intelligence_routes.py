from flask import Blueprint, request, jsonify
from core.financial_state import FinancialState
from services.intelligence_service import IntelligenceService

intelligence_bp = Blueprint("intelligence", __name__)
service = IntelligenceService()

@intelligence_bp.route("/intelligence/insights", methods=["POST"])
def get_insights():
    data = request.get_json(silent=True) or {}

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
        return jsonify({"insights": insights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

