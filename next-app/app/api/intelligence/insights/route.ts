import { NextResponse } from "next/server";
import { z } from "zod";
const schema = z.object({ income: z.coerce.number(), expenses: z.coerce.number(), savings: z.coerce.number(), debt: z.coerce.number(), risk_score: z.coerce.number(), investment_exposure: z.coerce.number(), goal_horizon_months: z.coerce.number().int(), emergency_fund_months: z.coerce.number() });
const insight = (category: string, severity: string, impact_area: string, message: string, confidence_score: number) => ({ category, severity, impact_area, confidence_score: Math.round(confidence_score * 1000) / 1000, message, created_at: new Date().toISOString(), explanation_ref: null });
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ detail: "Invalid financial state" }, { status: 400 });
  const s = parsed.data; const liquidity = s.expenses === 0 ? 0 : s.savings / s.expenses; const debtToIncome = s.income === 0 ? 0 : s.debt / s.income; const stability = Math.round((0.4 * Math.min(liquidity / 6, 1) + 0.3 * Math.min(s.emergency_fund_months / 6, 1) + 0.3 * (1 - Math.min(debtToIncome, 1))) * 1000) / 1000; const insights = [];
  if (s.risk_score < 0.4) insights.push(insight("threat", "high", "risk", "Elevated market volatility may impact low-risk portfolios", 0.85));
  if (liquidity < 3) insights.push(insight("threat", "medium", "liquidity", "Low liquidity buffer detected relative to monthly expenses", 0.8));
  if (debtToIncome > 0.5) insights.push(insight("threat", "high", "stability", "High debt-to-income ratio may reduce financial flexibility", 0.85));
  if (stability >= 0.75) insights.push(insight("stability", "low", "stability", "Overall financial position appears stable", 0.9));
  if (stability < 0.4) insights.push(insight("threat", "high", "stability", "Overall financial stability is under pressure", 0.9));
  return NextResponse.json({ insights });
}
