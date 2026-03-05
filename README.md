# Personalized AI-Driven Investment Planner

[Notion page for the project idea]
(https://www.notion.so/2-Personalized-AI-Driven-Investment-Planner-21cd1ee2d1be807da0a1e1693cd1f0c8)

**Live Web App:**  
https://ai-driven-invest-planner.vercel.app/

---

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
```
Frontend (Web UI)
↓
Backend API
↓
Decision Logic + AI Reasoning
↓
Database
```

Key rules:
- AI is **never** used to execute financial actions.
- AI outputs are structured, versioned, and logged.
- All numeric calculations (ROI, allocation limits) are deterministic.

---

## Tech Stack

### Frontend
- HTML, CSS, JavaScript
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
```
finpass-ai
├── backend/
│ ├── main.py
│ ├── requirements.txt
│ │
│ ├── core/
│ │ ├── insight.y
│ │ ├── market_state.py
│ │ ├── rule_engine.py
│ │ └── financial_state.py
│ ├── agent/
│ │ ├── decision_engine.py
│ │ ├── financial_agent.py
│ │ └── what_if.py
│ │
│ ├── analytics/
│ │ └── financial_analytics.py
│ │
│ ├── routes/
│ │ └── intelligence_routes.py 
│ │ 
│ ├── services/
│ │ └── intelligence_service.py
│ │
│ ├── ml/
│ │ ├── goal_intelligence.py
│ │ ├── goal_predictor.py
│ │ └── init.py
│ │
│ └── utils/
│   ├── data_normalizer.py
│   └── init.py
│
└── frontend/
  ├── dashboard.html
  ├── register.html
  ├── index.html
  ├── wizard.html
  │
  ├── css/
  │ └── style.css
  │
  └── js/
    ├── api.js
    ├── config.js
    ├── dashboard.js
    ├── login.js
    ├── register.js
    └── wizard.js
```
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
- New integration from Vertex and Gemini have been implemented that is currently in the development phase

---

## Disclaimer

FinPass AI is an **educational and advisory system**.  
It does not execute trades, manage funds, or provide legally binding financial advice.

All recommendations are intended to support user understanding and decision-making.

---

## Author

Developed as a focused, system-driven financial AI project with an emphasis on clarity, safety, and long-term thinking.

## Bugs

The Onboarding wizard is still facing the Continuation problem and i was thinking to branch it and solve it independently while making new changes to the functionality of the project.