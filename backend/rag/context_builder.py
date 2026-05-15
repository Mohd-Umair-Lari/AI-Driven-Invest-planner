

from typing import Any, Dict, List

def build_financial_context(ctx: Dict[str, Any]) -> str:

    if not ctx:
        return "No financial data available for this user."

    lines = [
        "=== USER FINANCIAL PROFILE ===",
        f"Name             : {ctx['name']}",
        f"Employment       : {ctx['employment_status']}",
        f"Age              : {ctx.get('age', 'N/A')}",
        "",
        "=== MONTHLY CASH FLOW ===",
        f"Monthly Income   : ₹{ctx['income']:,.0f}",
        f"Monthly Expenses : ₹{ctx['expenses']:,.0f}",
        f"Monthly Surplus  : ₹{ctx['surplus']:,.0f}",
        f"Savings Rate     : {ctx['savings_rate']}%",
        f"Outstanding Debt : ₹{ctx['debt']:,.0f}",
        f"Debt-to-Income   : {ctx['debt_ratio']}x",
        f"Emergency Fund   : {'Yes' if ctx['emergency_fund'] else 'No'}",
    ]

    categories = ctx.get("spending_categories", {})
    if categories:
        lines.append("")
        lines.append("=== SPENDING BY CATEGORY (THIS MONTH) ===")
        for cat, amount in sorted(categories.items(), key=lambda x: -x[1]):
            pct = round(amount / ctx["expenses"] * 100, 1) if ctx["expenses"] else 0
            lines.append(f"  {cat.capitalize():<20}: ₹{amount:,.0f}  ({pct}% of expenses)")

    transactions: List[Dict] = ctx.get("transactions", [])
    if transactions:
        lines.append("")
        lines.append(f"=== RECENT TRANSACTIONS ({len(transactions)} records) ===")
        for t in transactions[:15]:
            date  = t.get("date", "")[:10]
            cat   = t.get("category", "Other")
            desc  = t.get("description", "")
            amt   = t.get("amount", 0)
            ttype = t.get("type", "debit")
            sign  = "-" if ttype == "debit" else "+"
            lines.append(f"  {date}  {cat:<16} {sign}₹{abs(amt):,.0f}  {desc[:40]}")

    lines += [
        "",
        "=== FINANCIAL GOAL ===",
        f"Goal             : {ctx['goal_name']}",
        f"Target Amount    : ₹{ctx['target_amount']:,.0f}",
        f"Time Horizon     : {ctx['target_months']} months",
        f"Risk Appetite    : {ctx['risk'].capitalize()}",
        "",
        "=== INVESTMENT ===",
        f"Mode             : {ctx['invest_mode']}",
        f"Monthly Amount   : ₹{ctx['invest_amount']:,.0f}",
        f"Current Portfolio: ₹{ctx['current_portfolio']:,.0f}",
        f"Goal Probability : {ctx['goal_probability']}%",
    ]

    return "\n".join(lines)

def build_category_context(
    category: str,
    transactions: List[Dict],
    ctx: Dict[str, Any]
) -> str:

    if not transactions:
        stored_amount = ctx.get("spending_categories", {}).get(category, 0)
        if stored_amount:
            return (
                f"=== {category.upper()} SPENDING ===\n"
                f"Total this month : ₹{stored_amount:,.0f}\n"
                f"Total expenses   : ₹{ctx['expenses']:,.0f}\n"
                f"Share of budget  : {round(stored_amount / ctx['expenses'] * 100, 1) if ctx['expenses'] else 0}%"
            )
        return f"No {category} transaction data found."

    total = sum(abs(t.get("amount", 0)) for t in transactions if t.get("type") == "debit")
    lines = [
        f"=== {category.upper()} SPENDING BREAKDOWN ===",
        f"Total spent      : ₹{total:,.0f}",
        f"Total expenses   : ₹{ctx['expenses']:,.0f}",
        f"Share of budget  : {round(total / ctx['expenses'] * 100, 1) if ctx['expenses'] else 0}%",
        "",
        "Transactions:",
    ]
    for t in transactions:
        date = t.get("date", "")[:10]
        desc = t.get("description", "")
        amt  = abs(t.get("amount", 0))
        lines.append(f"  {date}  ₹{amt:,.0f}  {desc}")

    return "\n".join(lines)
