import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail } from "@/lib/request-auth";
export async function GET(request: Request, { params }: { params: Promise<{ email: string }> }) {
  const auth = await authorizedEmail(request); if (auth instanceof Response) return auth; const email = decodeURIComponent((await params).email); if (auth !== email.toLowerCase()) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const user = await (await getDb()).collection("userGoals").findOne({ email }); if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 }); const ob = user.onboarding ?? {};
  return NextResponse.json({ status: "success", onboarding: { state: ob.status, current_step: ob.current_step, data: ob.data ?? {} } });
}
