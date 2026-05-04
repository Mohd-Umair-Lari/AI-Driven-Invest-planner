from flask import Blueprint, request, jsonify
from ai.groq_client import generate_response

advisor_bp = Blueprint("advisor", __name__)


@advisor_bp.route("/advisor/chat", methods=["POST"])
def chat_advisor():
    """
    AI Financial Advisor Chatbot Endpoint
    Accepts user questions and returns AI-generated financial advice
    """
    data = request.get_json(silent=True) or {}
    
    user_question = data.get("question", "").strip()
    user_email = data.get("email", "").strip()
    
    if not user_question:
        return jsonify({"error": "Please provide a question"}), 400
    
    if not user_email:
        return jsonify({"error": "User email is required"}), 400
    
    try:
        # Build context-aware prompt for better responses
        context = data.get("context", {})
        monthly_income = context.get("monthly_income", 0)
        monthly_expenses = context.get("monthly_expenses", 0)
        total_savings = context.get("total_savings", 0)
        debt = context.get("debt", 0)
        risk_appetite = context.get("risk_appetite", "Moderate")
        
        # Enhance the prompt with user's financial context
        enhanced_prompt = f"""
        You are FinPass AI, a knowledgeable financial advisor. Help the user with personalized financial advice based on their situation:
        
        User's Financial Profile:
        - Monthly Income: ₹{monthly_income:,}
        - Monthly Expenses: ₹{monthly_expenses:,}
        - Total Savings: ₹{total_savings:,}
        - Current Debt: ₹{debt:,}
        - Risk Appetite: {risk_appetite}
        
        User Question: {user_question}
        
        Provide clear, actionable financial advice. Be specific and reference their numbers when relevant.
        Keep response concise but comprehensive.
        """
        
        # Generate AI response using Groq
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
