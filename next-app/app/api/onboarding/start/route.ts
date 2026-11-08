import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail } from "@/lib/request-auth";
export async function POST(request: Request) {
  const auth = await authorizedEmail(request); if (auth instanceof Response) return auth; const { email } = await request.json(); if (auth !== String(email).toLowerCase()) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const users = (await getDb()).collection("userGoals"); const user = await users.findOne({ email }); if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  const onboarding = ["not_started", "cancelled"].includes(user.onboarding?.status) ? { status: "in_progress", current_step: 0, last_updated: new Date().toISOString() } : user.onboarding ?? { status: "in_progress", current_step: 0 };
  await users.updateOne({ email }, { $set: { onboarding } }); return NextResponse.json({ status: "success", onboarding });
}
