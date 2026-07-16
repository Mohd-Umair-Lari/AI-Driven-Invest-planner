---
title: FinPass
emoji: 📈
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# FinPass — Financial Planner + Advisor

> **Live App:** [https://ai-driven-invest-planner.vercel.app](https://ai-driven-invest-planner.vercel.app)  
> **Original Concept:** [Notion — Personalized AI-Driven Investment Planner](https://www.notion.so/2-Personalized-AI-Driven-Investment-Planner-21cd1ee2d1be807da0a1e1693cd1f0c8)

---

## What Is FinPass?

**FinPass** is a **Financial Planner + Advisor** — a full-stack app for Indian investors that combines deterministic financial planning with Groq-powered LLaMA-3 AI. It generates personalized investment plans, goal projections, and actionable insights through a clean, responsive web dashboard.

The app is designed around three principles:

| Principle | What it means in practice |
|---|---|
| **Explainability over hype** | Every recommendation comes with a rationale. No black-box outputs. |
| **Discipline over greed** | Recommendations focus on SIPs, diversification, and long-term wealth — not speculation. |
| **System-led, AI-assisted** | Deterministic math governs all calculations (SIP future value, goal probability, asset allocation). AI is used only for interpretation and natural-language explanation. |

---

## How It Works — Core Flow

```
User registers → Onboarding Wizard (3 steps) → Dashboard
                                                    │
                                        ┌───────────┴───────────┐
                                        ▼                       ▼
                               Goal Intelligence         AI Advisor Chat
                          (SIP math + Monte Carlo)   (Groq LLaMA-3 analysis)
                                        │                       │
                                        └───────────┬───────────┘
                                                    ▼
                                         Personalized Dashboard
                              (Stat cards · Cash flow · Goal bar · Insights)
```

### Step-by-Step User Journey

1. **Landing page** (`/`) — Introduction to the app; links to Sign In / Get Started.
2. **Register** (`/register.html`) — Creates account (name, email, password, age, employment).
3. **Onboarding Wizard** (`/wizard.html`) — 3-step form collecting:
   - Financial Goal (goal type, target amount, timeline)
   - Monthly Financials (income, expenses, debt, emergency fund)
   - Investment Preferences (risk appetite, investment mode, SIP amount)
4. **Dashboard** (`/dashboard.html`) — Personalized analytics hub with 5 tabs.

---

## Dashboard — Features

### Tab 1: Overview (Main Dashboard)
- **4 Stat Cards**: Monthly Income · Total Portfolio · Goal Target · Monthly Debt
- **Cash Flow Donut Chart** (Chart.js): Breaks income into Debt / Investable Surplus / Living Expenses
- **Goal Progress Bar**: Live probability of reaching financial goal (from `/api/goal-intelligence`)
- **AI Advisor Panel**: Two static insights + live chatbot input (asks AI about your portfolio)
- **Recommended Actions**: Tax filing, SIP top-ups, insurance review

### Tab 2: Cash Flow Analysis
- Stacked proportional bar showing where income goes (Expenses · Debt · Investments · Surplus)
- Detailed allocation rows with mini progress bars and ₹ values
- Summary metrics: Savings Rate · Debt Ratio · Expense Ratio

### Tab 3: Wealth Reports
- Placeholder — planned for PDF generation and tax-saving strategy reports

### Tab 4: My Profile
- Read-only view of all profile data
- Edit form: update name, age, employment status, income, expenses, risk appetite
- Changes saved via `PUT /api/user/<email>` and reflected instantly in the dashboard

### Tab 5: Preferences
- Email notification and SMS alert toggles (UI complete)

---

## Intelligence Engine — How the Numbers Work

### Goal Intelligence (`/api/goal-intelligence/<email>`)
Uses compound interest SIP future value formula:

```
FV = P × [(1 + r)^n − 1] / r
```

Where:
- `P` = monthly savings (income − expenses)
- `r` = monthly ROI (Low: 6% / Moderate: 10% / High: 14% annualized)
- `n` = goal timeline in months

Returns: expected corpus, probability %, gap to goal, and a human-readable verdict.

### Goal Probability (`/api/predict/<email>`)
Runs **1,000 Monte Carlo simulations** with Gaussian noise on monthly returns to compute the statistical likelihood of hitting the target amount.

### AI Financial Analysis (`/api/analyze-finances/<email>`)
Sends user's full financial profile to **Groq LLaMA-3.1-8b-instant** and requests:
- A health score (0–100)
- 2–3 sentence honest assessment
- 3 specific actionable recommendations
- Investment allocation (equity/debt/cash, must sum to 100%)

If Groq is unavailable, a deterministic rule-based fallback computes the same fields using savings rate and debt-to-income ratio.

### Asset Allocation (Risk-Based)
| Risk Level | Equity | Debt | Gold |
|---|---|---|---|
| Low | 30% | 60% | 10% |
| Moderate | 60% | 30% | 10% |
| High | 80% | 15% | 5% |

---

## Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| Structure | HTML5 (semantic) |
| Styling | Vanilla CSS (`style.css`) + Tailwind CSS CDN |
| Charts | Chart.js |
| Scripting | Vanilla JavaScript (ES modules) |
| Fonts | Google Fonts — Inter |
| Theme | Dark/Light toggle via `.dark` class on `<html>` |
| Deployment | **Vercel** |

### Backend
| Layer | Technology |
|---|---|
| Framework | Python Flask 3.0 |
| AI | Groq SDK — `llama-3.1-8b-instant` |
| Database | MongoDB Atlas (via PyMongo + Certifi TLS) |
| Auth | Werkzeug password hashing (scrypt/pbkdf2) |
| Deployment | **Hugging Face Spaces** (primary) |
| Process Manager | Gunicorn (2 workers, 4 threads, gthread class) |

---

## Project Structure

```
AI-Financial Advisor/
├── Procfile                          ← gunicorn startup config
├── vercel.json                       ← root-level JS MIME type headers
│
├── backend/
│   ├── main.py                       ← Flask app + all core API routes (21 endpoints)
│   ├── groq_service.py               ← Groq AI client initialisation + financial insights
│   ├── requirements.txt
│   ├── .env                          ← MONGO_URI, GROQ_API_KEY, DB_NAME, PORT
│   │
│   ├── ai/
│   │   ├── groq_client.py            ← generate_response(prompt)
│   │   ├── prompts.py                ← investment_explanation_prompt(), financial_analysis_prompt()
│   │   └── formatter.py             ← clean_response() JSON cleaner
│   │
│   ├── ml/
│   │   ├── goal_intelligence.py      ← SIP FV formula + verdict engine
│   │   └── goal_predictor.py        ← Monte Carlo simulation, asset_allocation(), generate_plan()
│   │
│   ├── analytics/
│   │   └── financial_analytics.py   ← compute_financial_health()
│   │
│   ├── core/
│   │   ├── financial_state.py        ← FinancialState dataclass (liquidity, stability score)
│   │   ├── insight.py
│   │   ├── market_state.py
│   │   └── rule_engine.py           ← Deterministic rule-based insight engine
│   │
│   ├── agent/
│   │   ├── financial_agent.py        ← run_agent() — AI action decision system
│   │   ├── decision_engine.py
│   │   └── what_if.py               ← What-if scenario analysis
│   │
│   ├── adapter/
│   │   └── market_adapter.py
│   │
│   ├── services/
│   │   └── intelligence_service.py  ← Wraps rule engine for insight generation
│   │
│   └── routes/
│       ├── advisor_routes.py         ← POST /api/advisor/chat (chatbot)
│       └── intelligence_routes.py   ← POST /api/intelligence/insights
│
└── frontend/
    ├── vercel.json                   ← URL rewrites: /login.html → /static/login.html
    ├── css/
    │   └── style.css                 ← Master stylesheet (dark/light CSS variables)
    ├── js/
    │   ├── config.js                 ← BACKEND_URL (dev vs. prod switcher)
    │   ├── api.js                    ← apiFetch() with 60s timeout + error handling
    │   ├── theme.js                  ← Dark/light toggle, localStorage persistence
    │   ├── dashboard.js              ← Dashboard logic (charts, chatbot, profile, tabs)
    │   ├── login.js                  ← Login form handler
    │   ├── register.js               ← Registration form handler
    │   ├── wizard.js                 ← Multi-step onboarding wizard logic
    │   └── advisor.js                ← Dedicated AI advisor page
    └── static/                       ← All HTML pages
        ├── index.html                ← Landing page
        ├── login.html
        ├── register.html
        ├── wizard.html
        ├── dashboard.html
        └── advisor.html
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/test-connection` | MongoDB ping |
| POST | `/api/login` | Authenticate user |
| POST | `/api/signup` | Register new user |
| POST | `/api/onboarding/start` | Start wizard session |
| POST | `/api/onboarding/save` | Save wizard step data |
| POST | `/api/onboarding/cancel` | Pause onboarding |
| GET | `/api/onboarding/status/<email>` | Get onboarding state |
| POST | `/api/onboarding/complete` | Mark onboarding complete |
| GET | `/api/user/<email>` | Fetch user profile |
| PUT | `/api/user/<email>` | Update user profile |
| GET | `/api/analytics/<email>` | Financial health metrics |
| GET | `/api/predict/<email>` | Monte Carlo goal probability |
| GET | `/api/recommend/<email>` | Asset allocation plan |
| GET | `/api/goal-intelligence/<email>` | SIP FV + verdict + gap |
| GET | `/api/analyze-finances/<email>` | Full Groq AI analysis |
| POST | `/api/init-test-data/<email>` | Seed test financial data |
| GET | `/api/ai/investment-insight/<email>` | AI investment insight |
| GET | `/api/agent/<email>` | AI agent decision (HOLD/BUY/REBALANCE) |
| POST | `/api/advisor/chat` | Chatbot Q&A with financial context |
| POST | `/api/intelligence/insights` | Rule-based insight engine |

---

## Environment Variables

```env
MONGO_URI=mongodb+srv://...         # MongoDB Atlas connection string
DB_NAME=mockDB                      # Database name
COLLECTION_NAME=userGoals           # Collection name
GROQ_API_KEY=gsk_...                # Groq API key (LLaMA-3 access)
PORT=5000                           # Server port
```

---

## Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
# Runs on http://localhost:5000
```

### Frontend
Open `frontend/static/index.html` in a browser, or serve with any static server:
```bash
npx serve frontend
# Vercel dev: vercel dev (from frontend/)
```

The `config.js` automatically switches `BACKEND_URL` between `localhost:5000` (dev) and the Hugging Face production URL.

---

## Deployment

| Service | Hosts | URL |
|---|---|---|
| **Vercel** | Frontend (`frontend/` root) | `https://ai-driven-invest-planner.vercel.app` |
| **Hugging Face Spaces** | Backend Flask API | `https://umairlari-ai-financial-advisor-backend.hf.space` |

The `frontend/vercel.json` maps legacy root URLs to the new `static/` folder:
```json
{ "source": "/login.html", "destination": "/static/login.html" }
```

---

## Known Limitations / In Progress

- **AI Chatbot**: The chatbot UI is live, but responses are currently simulated. Connection to the `/api/advisor/chat` backend endpoint is pending.
- **Cash Flow tab**: Allocation figures are static placeholder values, not yet dynamically pulled from user data.
- **Wealth Reports tab**: Placeholder — PDF report generation not yet implemented.
- **Preferences tab**: Toggle UI is complete; backend persistence is not yet wired.

---

## Disclaimer

FinPass is an **educational and informational tool** only.  
It does not execute trades, manage funds, or provide legally binding financial advice.  
All investment data shown is for illustrative purposes.  
Please consult a SEBI-registered investment advisor before making significant financial decisions.

---

The agent earlier used for the build is Kimi2.6 model API's from OpenRouter and the LLM used is Groq 5.1
the work is still in progress and can be completed after the exams i guess and will try to update the ap as far as possible 

@ all rights reserved to Umair Lari