import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail } from "@/lib/request-auth";
export async function POST(request: Request) {
  const auth = await authorizedEmail(request); if (auth instanceof Response) return auth; const { email, step = 0, payload = {} } = await request.json(); if (auth !== String(email).toLowerCase()) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const users = (await getDb()).collection("userGoals"); const user = await users.findOne({ email }); if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  await users.updateOne({ email }, { $set: { "onboarding.status": "in_progress", "onboarding.current_step": step, "onboarding.data": { ...(user.onboarding?.data ?? {}), ...payload }, "onboarding.last_updated": new Date().toISOString() } }); return NextResponse.json({ status: "saved" });
}
