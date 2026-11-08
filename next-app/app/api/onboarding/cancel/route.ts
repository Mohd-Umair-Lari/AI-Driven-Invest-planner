import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail } from "@/lib/request-auth";
export async function POST(request: Request) {
  const auth = await authorizedEmail(request); if (auth instanceof Response) return auth; const { email, current_step } = await request.json(); if (auth !== String(email).toLowerCase()) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const set: Record<string, unknown> = { "onboarding.status": "cancelled", "onboarding.last_updated": new Date().toISOString() }; if (current_step !== undefined) set["onboarding.current_step"] = current_step;
  await (await getDb()).collection("userGoals").updateOne({ email }, { $set: set }); return NextResponse.json({ status: "cancelled" });
}
