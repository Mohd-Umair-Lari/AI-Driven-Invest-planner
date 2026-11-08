import { NextResponse } from "next/server";
import { z } from "zod";
import { getDb } from "@/lib/mongo";
import { env } from "@/lib/env";
import { Resend } from "resend";
import crypto from "node:crypto";
const schema = z.object({ email: z.string().email() });
const generic = { success: true, message: "If an account exists with this email, you will receive a password reset link shortly." };
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ detail: "Valid email is required" }, { status: 400 });
  const email = parsed.data.email.toLowerCase();
  const db = await getDb();
  const user = await db.collection<any>("userGoals").findOne({ email });
  if (!user) return NextResponse.json(generic);
  const token = crypto.randomBytes(32).toString("base64url");
  const hash = crypto.createHash("sha256").update(token).digest("hex");
  await db.collection("passwordResetTokens").insertOne({ email, token_hash: hash, expires_at: new Date(Date.now() + 86400000), used: false });
  if (env.resendApiKey) { const resend = new Resend(env.resendApiKey); await resend.emails.send({ from: process.env.RESEND_FROM_EMAIL ?? "onboarding@resend.dev", to: email, subject: "Reset your FinPass AI password", html: `<p><a href="${env.appUrl}/reset_password.html?token=${encodeURIComponent(token)}">Reset password</a></p>` }); }
  return NextResponse.json(generic);
}
