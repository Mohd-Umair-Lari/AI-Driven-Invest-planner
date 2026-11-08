import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail } from "@/lib/request-auth";
export async function POST(request: Request) {
  const auth = await authorizedEmail(request); if (auth instanceof Response) return auth; const { email } = await request.json(); if (auth !== String(email).toLowerCase()) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const users = (await getDb()).collection("userGoals"); const user = await users.findOne({ email }); if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 }); const data = user.onboarding?.data ?? {};
  const set: Record<string, unknown> = { "onboarding.status": "completed", "onboarding.current_step": null, "onboarding.last_updated": new Date().toISOString(), "onboarding.data": data }; if (data.name) set.Name = data.name; if (data.age) set.Age = String(data.age); if (data.employment_status) set["employment-status"] = data.employment_status;
  const financials = { ...(user.financials ?? {}) }; if (data.monthly_income || data["monthly-income"]) financials["monthly-income"] = data.monthly_income || data["monthly-income"]; if (data.monthly_expenses || data["monthly-expenses"]) financials["monthly-expenses"] = data.monthly_expenses || data["monthly-expenses"]; set.financials = financials;
  await users.updateOne({ email }, { $set: set }); return NextResponse.json({ status: "completed" });
}
