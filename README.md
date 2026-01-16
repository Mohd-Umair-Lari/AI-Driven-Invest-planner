# Personalized-AI-Driven-Investment-Planner

[The Notion page for the idea of the Project lies here](https://www.notion.so/2-Personalized-AI-Driven-Investment-Planner-21cd1ee2d1be807da0a1e1693cd1f0c8)

The WebApp is live at : https://ai-driven-invest-planner.vercel.app/

# FinPass AI

FinPass AI is a financial planning web application designed to help individuals understand, structure, and optimize their investment journey in a calm, explainable, and disciplined way.

Rather than focusing on short-term trading or aggressive predictions, FinPass AI emphasizes **investment routes**, **long-term planning**, and **behavior-aware recommendations** that adapt to users over time.

---

## Project Philosophy

FinPass AI is built on three core principles:

- **Explainability over hype**  
  Every recommendation is reasoned, structured, and understandable.

- **Discipline over greed**  
  The system avoids frequent or impulsive changes and prioritizes financial stability.

- **System-led decisions, AI-assisted reasoning**  
  Deterministic logic governs money-related rules, while AI is used strictly for interpretation, evaluation, and explanation.

---

## Key Features

### 1. Investment Route Generator
FinPass AI generates curated investment routes based on a user’s income profile, risk appetite, and investment horizon.

Supported user categories:
- **Daily wage earners**: RD, Post Office schemes, Sovereign Gold Bonds
- **Salaried individuals**: SIPs, ELSS, PPF, NPS
- **High Net-Worth Individuals (HNIs)**: Stocks, REITs, Mutual Funds, equity baskets

Each route includes:
- Asset allocation rationale
- Short-, mid-, and long-term ROI simulations
- Clear explanations instead of opaque numbers

---

### 2. Adaptive Recommendation Updates
The system periodically evaluates whether a user’s current investment route should be adjusted, based on:

- Simulated market regimes
- Policy and macroeconomic signals
- User behavior (missed investments, expense spikes, consistency)

To avoid overwhelm:
- Recommendations are rate-limited
- Confidence thresholds are enforced
- Large changes require strong justification

---

## Architecture Overview

FinPass AI follows a simple, robust architecture:

Frontend (Web UI) -> Backend API -> Decision Logic + AI Reasoning -> DataBase


- AI is **never** used to execute financial actions.
- AI outputs are structured, versioned, and logged.
- All numeric calculations (ROI, allocation limits) are deterministic.

---

## Tech Stack

### Frontend
- Modern JavaScript framework (Vite/React-based)
- Deployed on **Vercel**

### Backend
- Python-based API (Flask / FastAPI)
- Deployed on **Render**

### Database
- Non-relational database (schema-controlled at application level)

### Deployment Model
- Monorepo structure with separate `frontend/` and `backend/` directories
- Independent deployments for frontend and backend
- Public URLs for external testing and validation

---

## Repository Structure

'''
finpass-ai/
|-- frontend/
|   |-- css/
|   |-- js/
|   |-- dashboard.html
|   |-- register.html
|   |-- wizard.html
|   `-- index.html
|
|-- backend/
|   |-- app.py
|   |-- requirements.txt
|   |-- analytics/
|   |-- ml/
|   `-- agent/
|
|-- README.md
`-- .gitignore
'''

---

## Deployment Status

The project is publicly deployed and accessible via:
- **Frontend**: Vercel
- **Backend**: Render

The application has been tested across multiple devices and networks to ensure external accessibility and correct frontend–backend communication.

---

## Current Stage

- Core architecture finalized
- Deployment pipeline stabilized
- Feature set validated end-to-end

Upcoming work focuses on:
- Refining UX and explanations
- Expanding investment logic depth
- Improving behavioral signal modeling
- Hardening edge cases and safeguards

---

## Disclaimer

FinPass AI is an **educational and advisory system**.  
It does not execute trades, manage funds, or provide legally binding financial advice.

All recommendations are intended to support user understanding and decision-making.

---

## Author

Developed as a focused, system-driven financial AI project with an emphasis on clarity, safety, and long-term thinking.
