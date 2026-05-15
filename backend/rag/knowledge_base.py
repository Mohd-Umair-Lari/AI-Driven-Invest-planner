"""
rag/knowledge_base.py
----------------------
Curated India-specific financial knowledge base.
- Seeded once into MongoDB on startup.
- Each chunk is embedded and stored for semantic retrieval.
- Topics: SIP, ELSS, PPF, NPS, EMI, tax slabs, emergency funds,
          asset allocation, rebalancing, insurance, debt strategies.
"""
from typing import List, Tuple

# ── (doc_id, text) tuples ──────────────────────────────────────
KNOWLEDGE_CHUNKS: List[Tuple[str, str]] = [

    # ── SIP & Mutual Funds ─────────────────────────────────────
    ("sip_basics", """
SIP (Systematic Investment Plan) allows you to invest a fixed amount in a mutual fund at regular intervals (monthly/weekly).
Benefits: Rupee cost averaging, compounding over time, low entry barrier (₹500/month minimum).
Best for: Long-term wealth creation (5+ years), beating inflation, goal-based investing.
Rule of thumb: Increase SIP by 10% every year (step-up SIP) to compensate for inflation and salary hikes.
"""),

    ("mutual_fund_categories", """
Mutual Fund Categories in India:
- Equity Funds: High risk, high return (10-15% CAGR long-term). Best for 5+ year horizons.
- Debt Funds: Low risk, stable return (6-8%). Good for 1-3 year goals or capital preservation.
- Hybrid Funds: Balanced mix of equity + debt (8-11% CAGR). Moderate risk.
- ELSS (Equity Linked Savings Scheme): Tax-saving mutual fund (80C). 3-year lock-in. Equity exposure.
- Index Funds: Track Nifty/Sensex. Low expense ratio (<0.1%). Ideal for passive investors.
- Liquid Funds: Ultra-short-term debt. Better than savings account for emergency corpus.
"""),

    ("sip_corpus_calculation", """
SIP Future Value Formula: FV = P × [((1 + r)^n - 1) / r] × (1 + r)
Where P = monthly SIP, r = monthly return rate, n = number of months.
Example: ₹10,000/month SIP for 10 years at 12% annual return → corpus ≈ ₹23.2 lakhs.
Example: ₹15,000/month SIP for 20 years at 12% annual return → corpus ≈ ₹1.5 crores.
The power of compounding is strongest in the last few years — do not withdraw early.
"""),

    # ── Tax Planning ───────────────────────────────────────────
    ("tax_80c", """
Section 80C Deductions (India FY 2024-25):
Maximum limit: ₹1,50,000 per year.
Eligible investments: ELSS mutual funds, PPF, NSC, 5-year FD, life insurance premium, EPF contribution, principal repayment of home loan, tuition fees.
Strategy: ELSS is preferred as it has shortest lock-in (3 years) + equity returns.
PPF is best for risk-averse investors: tax-free returns (~7.1% p.a.), 15-year lock-in.
"""),

    ("new_tax_regime", """
India New Tax Regime FY 2024-25 (default from FY 2024-25):
- Upto ₹3 lakh: NIL
- ₹3-7 lakh: 5%
- ₹7-10 lakh: 10%
- ₹10-12 lakh: 15%
- ₹12-15 lakh: 20%
- Above ₹15 lakh: 30%
Standard deduction: ₹75,000 (increased in Budget 2024).
Note: No HRA, 80C, 80D deductions in new regime. Choose old regime if deductions > ₹3.75 lakh.
Rebate u/s 87A: Zero tax upto ₹7 lakh net taxable income in new regime.
"""),

    ("tax_80d_nps", """
Section 80D (Health Insurance): Up to ₹25,000 for self+family. ₹50,000 for senior citizens.
Section 80CCD(1B) NPS: Additional ₹50,000 deduction beyond 80C limit for NPS contribution.
Section 24 (Home Loan Interest): Up to ₹2 lakh deduction on interest paid for self-occupied property.
HRA exemption: Min of [Actual HRA, 50% of basic (metro)/40% (non-metro), Rent paid - 10% of basic].
Capital Gains: STCG on equity > 1 year holding = 20% (revised). LTCG on equity > 1 year = 12.5% above ₹1.25L.
"""),

    # ── Emergency Fund ─────────────────────────────────────────
    ("emergency_fund", """
Emergency Fund: A liquid reserve covering 6 months of expenses (3 months minimum).
Purpose: Job loss, medical emergency, major repair — without liquidating investments.
Where to keep: Liquid mutual funds, high-interest savings account, sweep-in FD.
Rule: Never invest emergency fund in equity. It must be accessible within 1-2 days.
Calculation: If monthly expenses = ₹40,000 → Emergency fund target = ₹2,40,000 (6 months).
"""),

    # ── Debt Management ────────────────────────────────────────
    ("debt_management", """
Debt Repayment Strategies:
1. Avalanche Method: Pay highest interest rate debt first (saves most money).
2. Snowball Method: Pay smallest balance first (builds psychological momentum).
Healthy debt-to-income ratio: EMI should not exceed 40% of take-home salary.
Bad debt: Credit card (30-42% p.a.), personal loans (12-24% p.a.) — repay immediately.
Good debt: Home loan (8-9% p.a.) — tax deductible, asset appreciates.
Pre-payment strategy: Use annual bonus to reduce loan principal → reduces tenure significantly.
"""),

    # ── Asset Allocation ───────────────────────────────────────
    ("asset_allocation", """
Asset Allocation by Age (thumb rule): Equity % = 100 - Age
Age 25: 75% equity, 25% debt
Age 35: 65% equity, 35% debt
Age 45: 55% equity, 45% debt
Age 55: 45% equity, 55% debt

Risk-based allocation:
- Conservative: 30% equity, 60% debt, 10% gold
- Moderate: 60% equity, 30% debt, 10% gold
- Aggressive: 80% equity, 15% debt, 5% gold

Rebalance portfolio every 12 months or when allocation drifts >10% from target.
"""),

    # ── PPF & NPS ──────────────────────────────────────────────
    ("ppf_nps", """
PPF (Public Provident Fund):
- Interest rate: 7.1% p.a. (tax-free, compounded annually)
- Lock-in: 15 years (partial withdrawal from Year 7)
- Max investment: ₹1.5 lakh/year. Min: ₹500/year.
- Triple tax benefit (EEE): Deposit deductible (80C), returns tax-free, maturity tax-free.

NPS (National Pension System):
- Market-linked. Equity allocation up to 75% (Tier I).
- 80CCD(1): Deduction up to 10% of salary (within 80C limit).
- 80CCD(1B): Additional ₹50,000 deduction.
- At retirement: 60% lump sum (tax-free), 40% must buy annuity.
"""),

    # ── Insurance ──────────────────────────────────────────────
    ("term_insurance", """
Term Life Insurance:
- Pure protection — no maturity benefit. Premium much lower than endowment plans.
- Rule: Cover = 10-15x annual income.
- Example: Annual income ₹10 lakh → Cover ₹1-1.5 crore.
- Best age to buy: 25-35 (cheapest premiums). Increases significantly after 40.
- Features to look for: Accidental death benefit, critical illness rider, return of premium option.
- Avoid ULIPs and endowment plans — mix of investment + insurance is bad for both.

Health Insurance:
- Family floater: ₹10-25 lakh cover recommended.
- Super top-up plan: Covers above your base policy limit at low premium.
"""),

    # ── Goal Planning ──────────────────────────────────────────
    ("goal_planning", """
Financial Goal Planning Framework:
1. Define goal: Name, target amount, timeline.
2. Adjust for inflation: Future value = PV × (1 + inflation)^years. Use 6% inflation.
3. Calculate required SIP: Work backwards from future corpus.
4. Choose right instrument based on timeline:
   - < 1 year: Liquid fund, FD
   - 1-3 years: Debt fund, balanced advantage fund
   - 3-5 years: Hybrid fund
   - 5+ years: Equity mutual fund, direct stocks

Common goals:
- Child education: 15-18 years horizon (equity focus)
- Retirement: 20-30 years (equity + NPS)
- House down payment: 3-5 years (hybrid/debt)
- Car: 2-3 years (debt fund + RD)
"""),

    # ── Budgeting ──────────────────────────────────────────────
    ("50_30_20_rule", """
50-30-20 Budget Rule:
- 50% of income: Needs (rent, food, utilities, EMIs, insurance)
- 30% of income: Wants (dining out, entertainment, shopping, travel)
- 20% of income: Savings & investments (SIP, PPF, emergency fund, loan prepayment)

Indian adaptation (high savings culture):
- 40% needs, 20% wants, 40% savings (more aggressive savings rate recommended)
Savings rate benchmark:
- < 10%: Needs immediate attention
- 10-20%: Average
- 20-30%: Good
- > 30%: Excellent
"""),

    # ── Inflation & FD ─────────────────────────────────────────
    ("inflation_fd", """
Inflation in India:
- Average CPI inflation: 5-6% p.a.
- Real return = Nominal return - Inflation rate.
- FD returning 7% with 6% inflation = only 1% real return. Post-tax even lower.
- Equity markets (Nifty 50) historical return: 12-14% CAGR → real return of 6-8%.

Fixed Deposit considerations:
- Interest is fully taxable as per income slab.
- Senior citizen FDs: 0.25-0.5% extra interest.
- Tax-saving FD: 5-year lock-in, 80C deductible.
- Sweep-in FD: Linked to savings account, good for emergency fund parking.
"""),
]


def get_all_chunks() -> List[Tuple[str, str]]:
    """Return all (doc_id, text) pairs for seeding."""
    return [(doc_id, text.strip()) for doc_id, text in KNOWLEDGE_CHUNKS]
