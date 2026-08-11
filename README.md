---
title: FinPass AI
emoji: 📈
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

<div align="center">

<img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge" />
<img src="https://img.shields.io/badge/Frontend-Vercel-black?style=for-the-badge&logo=vercel" />
<img src="https://img.shields.io/badge/Backend-HuggingFace-yellow?style=for-the-badge&logo=huggingface" />
<img src="https://img.shields.io/badge/AI-Groq%20LLaMA--3-blueviolet?style=for-the-badge" />
<img src="https://img.shields.io/badge/DB-MongoDB%20Atlas-green?style=for-the-badge&logo=mongodb" />

# FinPass AI
### *Your Personal AI Financial Advisor — Built for India's Future Investors*

**[🚀 Try Live App](https://ai-driven-invest-planner.vercel.app)** &nbsp;·&nbsp; **[📖 Full Docs](./docs/PRODUCT_DOCS.md)** &nbsp;·&nbsp; **[🖼 Screenshots](./docs/SCREENSHOTS.md)**

</div>

---

## ❌ The Problem

Most Indians earn enough to build real wealth — but **never do**.

Not because they don't try. But because the system is broken:

- 💸 **No one explains where their money actually goes** — expenses, debt, and lifestyle creep silently consume every rupee of surplus
- 📉 **Generic advice doesn't work** — "invest in SIPs" means nothing without knowing *how much*, *in what*, and *for how long*, tailored to *your* income
- 🧮 **Planning tools are either too complex or too shallow** — spreadsheets intimidate beginners; generic apps give useless blanket advice
- 🔮 **People invest blind** — no way to simulate outcomes, stress-test goals, or see if they're on track
- 🤖 **AI tools exist — but not for personal finance in India** — no product combines real financial math with conversational AI in a single accessible platform

**The result?** Millions of earning Indians leave their money idle in savings accounts, missing a decade of compounding returns.

---

## ✅ The Solution — FinPass AI

**FinPass AI** is a full-stack, AI-powered financial advisor built for Indian investors. It combines rigorous financial mathematics with Groq-powered LLaMA-3 AI to give you:

> *A personalized investment plan, goal probability forecast, and a conversational AI advisor — all in one intelligent dashboard.*

You input your financials once. FinPass AI tells you exactly:
- **Where your money is going** (visual cash flow breakdown)
- **Whether you'll hit your goal** (Monte Carlo probability with 1,000 simulations)
- **How to allocate your investments** (risk-adjusted asset allocation)
- **What to do next** (AI-generated, context-aware action plan)

No spreadsheets. No jargon. No guessing.

---

## 🎯 Who Is It For?

| Profile | What FinPass AI Does For Them |
|---|---|
| 🧑‍💼 **Salaried Professionals** | Analyzes take-home pay, expenses & SIP capacity; shows retirement readiness |
| 🚀 **First-Time Investors** | Demystifies asset allocation — tells you exactly where to put your money |
| 🎓 **Young Adults (22–35)** | Shows the power of early investing through SIP projections and compounding math |
| 💼 **Self-Employed / Freelancers** | Handles variable income; sets conservative projections |
| 👨‍👩‍👧 **Goal-Oriented Families** | Tracks multiple financial goals — home, retirement, education — in one place |

---

## ⚡ Key Features

### 🧠 AI Financial Intelligence
- **Groq LLaMA-3 Analysis** — Sends your full financial profile to LLaMA-3.1-8b-instant and returns a personalized health score (0–100), honest assessment, and 3 actionable recommendations
- **Conversational AI Advisor** — Chat with an AI that *knows your portfolio* — ask anything about your finances in plain English
- **Graceful Fallback** — If AI is unavailable, a deterministic rule engine computes the same fields instantly

### 📊 Goal Intelligence Engine
- **SIP Future Value Formula** — Calculates your projected corpus at goal maturity:
  ```
  FV = P × [(1 + r)^n − 1] / r
  ```
  Where `P` = monthly surplus, `r` = monthly return rate, `n` = timeline in months
- **Monte Carlo Simulation** — Runs 1,000 simulations with Gaussian noise to compute statistical goal probability
- **Gap Analysis** — Shows exactly how far you are from your target and what it takes to close the gap
- **Plain-English Verdicts** — "On Track · Slightly Behind · Needs Immediate Attention"

### 💹 Cash Flow Analysis
- Full visual breakdown of income → Expenses · Debt · Investments · Surplus
- Live progress bars with ₹ values for every allocation category
- Key financial ratios: Savings Rate · Debt-to-Income · Expense Ratio

### 📈 Smart Asset Allocation (Risk-Based)
| Risk Appetite | Equity | Debt | Gold |
|---|---|---|---|
| 🟢 Low | 30% | 60% | 10% |
| 🟡 Moderate | 60% | 30% | 10% |
| 🔴 High | 80% | 15% | 5% |

### 🖥 Personalized Dashboard
- Real-time stat cards: Monthly Income · Total Portfolio · Goal Target · Monthly Debt
- Interactive Chart.js donut for cash flow visualization
- Live goal probability progress bar (pulled from `/api/goal-intelligence`)
- AI Advisor chat panel embedded directly in the dashboard
- Dark / Light mode with glassmorphism UI

### 🧙‍♂️ Guided Onboarding Wizard
- 3-step guided setup: Financial Goal → Monthly Financials → Investment Preferences
- Session-saved — resume exactly where you left off
- Completed in under 5 minutes

---

## 🔄 How It Works

```
User Registers → Onboarding Wizard (3 steps) → Dashboard
                                                    │
                                    ┌───────────────┴───────────────┐
                                    ▼                               ▼
                           Goal Intelligence Engine          AI Advisor Chat
                      (SIP FV Math + Monte Carlo)       (Groq LLaMA-3 Analysis)
                                    │                               │
                                    └───────────────┬───────────────┘
                                                    ▼
                                       Personalized Dashboard
                            (Stat Cards · Cash Flow · Goal Bar · Insights)
```

### Investment Route Logic
The system determines your investment recommendation by combining:
1. **Risk appetite** (Low / Moderate / High) set during onboarding wizard
2. **Investable surplus** = Monthly Income − Expenses − Debt EMI
3. **Goal timeline** — shorter timelines shift allocation toward safer debt instruments
4. **AI verdict** (HOLD / BUY / REBALANCE) — computed by the financial agent

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5 · Vanilla CSS (`style.css`) · Tailwind CDN · Chart.js · Google Fonts (Inter) |
| **Backend** | Python Flask 3.0 · Gunicorn (2 workers, 4 threads) |
| **AI Model** | Groq SDK · `llama-3.1-8b-instant` (temp 0.4 analysis / 0.5 chat) |
| **Database** | MongoDB Atlas via PyMongo + Certifi TLS |
| **Auth** | Werkzeug scrypt/pbkdf2 password hashing |
| **Frontend Deploy** | **Vercel** (static, `frontend/` root) |
| **Backend Deploy** | **Hugging Face Spaces** (Docker container) |

---

## 🚀 Live Deployment

| Service | Hosts | URL |
|---|---|---|
| **Vercel** | Frontend | [ai-driven-invest-planner.vercel.app](https://ai-driven-invest-planner.vercel.app) |
| **Hugging Face Spaces** | Backend Flask API | [umairlari-ai-financial-advisor-backend.hf.space](https://umairlari-ai-financial-advisor-backend.hf.space) |

---

## 🏗 Project Structure

```
AI-Financial Advisor/
├── backend/
│   ├── main.py                   ← Flask app + 21 API endpoints
│   ├── groq_service.py           ← Groq AI client + financial insights
│   ├── ai/                       ← LLaMA-3 client, prompts, response formatter
│   ├── ml/                       ← SIP math (goal_intelligence.py), Monte Carlo (goal_predictor.py)
│   ├── analytics/                ← compute_financial_health()
│   ├── core/                     ← Rule engine, FinancialState, MarketState
│   ├── agent/                    ← AI decision agent, what-if analysis
│   └── routes/                   ← /api/advisor/chat, /api/intelligence/insights
│
├── frontend/
│   ├── css/style.css             ← Master stylesheet (dark/light CSS variables, 1300+ lines)
│   ├── js/                       ← dashboard.js · wizard.js · api.js · theme.js · login.js
│   └── static/                   ← index.html · login.html · register.html · dashboard.html
│
└── docs/
    ├── PRODUCT_DOCS.md           ← Full product documentation
    └── SCREENSHOTS.md            ← Visual app walkthrough
```

---

## 📖 Documentation

| Document | Description |
|---|---|
| **[PRODUCT_DOCS.md](./docs/PRODUCT_DOCS.md)** | Full feature docs, user flows, recommendation logic, API reference |
| **[SCREENSHOTS.md](./docs/SCREENSHOTS.md)** | Visual walkthrough — every page of the live app |

---

## ⚙️ Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
# Create .env with: MONGO_URI, GROQ_API_KEY, DB_NAME, COLLECTION_NAME, PORT
python main.py
# Runs on http://localhost:5000
```

### Frontend
```bash
npx serve frontend
# config.js automatically switches BACKEND_URL between localhost:5000 and prod
```

---

## 🔐 Environment Variables

```env
MONGO_URI=mongodb+srv://...         # MongoDB Atlas connection string
DB_NAME=mockDB                      # Database name
COLLECTION_NAME=userGoals           # Collection name
GROQ_API_KEY=gsk_...                # Groq API key (LLaMA-3 access)
PORT=5000                           # Server port
```

---

## ⚠️ Disclaimer

FinPass AI is an **educational and informational tool** only. It does not execute trades, manage funds, or provide legally binding financial advice. All projections are illustrative. Please consult a SEBI-registered investment advisor before making significant financial decisions.

---

<div align="center">

Made with ❤️ by **Umair Lari** &nbsp;|&nbsp; © 2026 FinPass AI · All Rights Reserved

</div>