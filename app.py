"""Free Hugging Face Gradio entrypoint for FinPass AI."""

import os
import sys

import gradio as gr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from ai.groq_client import generate_response
from core.financial_state import FinancialState
from services.intelligence_service import IntelligenceService


def chat(question: str, email: str, income: float, expenses: float, savings: float, debt: float, risk: str) -> str:
    if not question.strip():
        return "Please enter a question."
    prompt = f"""You are FinPass AI, a professional personal finance advisor for Indian investors.
User email: {email or 'anonymous'}
Question: {question}
Monthly income: INR {income}
Monthly expenses: INR {expenses}
Savings: INR {savings}
Debt: INR {debt}
Risk appetite: {risk}
Give practical, educational guidance and clearly state that this is not regulated financial advice."""
    try:
        return generate_response(prompt)
    except Exception as exc:
        return f"The AI service is unavailable. Check GROQ_API_KEY in Space Settings. ({exc})"


def insights(income: float, expenses: float, savings: float, debt: float, risk_score: float, exposure: float, horizon: int, emergency: float):
    try:
        state = FinancialState(income, expenses, savings, debt, risk_score, exposure, horizon, emergency)
        return {"insights": IntelligenceService().run(state)}
    except Exception as exc:
        return {"error": str(exc)}


with gr.Blocks(title="FinPass AI") as demo:
    gr.Markdown("# FinPass AI\nPersonal finance guidance for Indian investors.")
    with gr.Tab("Advisor chat"):
        email = gr.Textbox(label="Email", placeholder="you@example.com")
        question = gr.Textbox(label="Question", lines=4)
        with gr.Row():
            income = gr.Number(label="Monthly income", value=0)
            expenses = gr.Number(label="Monthly expenses", value=0)
            savings = gr.Number(label="Savings", value=0)
            debt = gr.Number(label="Debt", value=0)
        risk = gr.Dropdown(["Conservative", "Moderate", "Aggressive"], value="Moderate", label="Risk appetite")
        ask = gr.Button("Ask FinPass AI", variant="primary")
        answer = gr.Markdown()
        ask.click(chat, [question, email, income, expenses, savings, debt, risk], answer)
    with gr.Tab("Financial insights"):
        values = [gr.Number(label=label, value=0) for label in ["Income", "Expenses", "Savings", "Debt", "Risk score", "Investment exposure", "Goal horizon (months)", "Emergency fund (months)"]]
        analyze = gr.Button("Generate insights", variant="primary")
        result = gr.JSON()
        analyze.click(insights, values, result)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
