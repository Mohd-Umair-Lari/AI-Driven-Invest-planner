from flask import Blueprint, request, jsonify
from ai.groq_client import generate_response

advisor_bp = Blueprint("advisor", __name__)

@advisor_bp.route("/advisor/chat", methods=["POST"])
def chat_advisor():

    data = request.get_json(silent=True) or {}

    user_question = data.get("question", "").strip()
    user_email = data.get("email", "").strip()

    if not user_question:
        return jsonify({"error": "Please provide a question"}), 400

    if not user_email:
        return jsonify({"error": "User email is required"}), 400

    try:

        context = data.get("context", {})
        monthly_income = context.get("monthly_income", 0)
        monthly_expenses = context.get("monthly_expenses", 0)
        total_savings = context.get("total_savings", 0)
        debt = context.get("debt", 0)
        risk_appetite = context.get("risk_appetite", "Moderate")

        enhanced_prompt = f

        ai_response = generate_response(enhanced_prompt)

        return jsonify({
            "success": True,
            "response": ai_response,
            "user_email": user_email
        }), 200

    except Exception as e:
        print(f"❌ Advisor error: {str(e)}")
        return jsonify({
            "error": "Failed to generate response",
            "details": str(e)
        }), 500
