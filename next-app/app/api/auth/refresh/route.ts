import { NextResponse } from "next/server";
import { z } from "zod";
import { getDb } from "@/lib/mongo";
import { createToken, verifyToken } from "@/lib/jwt";
const schema = z.object({ email: z.string().email(), refresh_token: z.string().min(1) });
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ detail: "email and refresh_token required" }, { status: 400 });
  const email = parsed.data.email.toLowerCase();
  const claims = await verifyToken(parsed.data.refresh_token, "refresh");
  if (!claims || claims.sub !== email) return NextResponse.json({ detail: "Invalid or expired refresh token" }, { status: 401 });
  const user = await getDb().then((db) => db.collection<any>("userGoals").findOne({ email }));
  if (!user) return NextResponse.json({ detail: "User not found" }, { status: 401 });
  return NextResponse.json({ access_token: await createToken(email, String(user._id), "access"), refresh_token: parsed.data.refresh_token, token_type: "bearer", expires_in: 900 });
}
