import { NextResponse } from "next/server";
import { z } from "zod";
import crypto from "node:crypto";
import { getDb } from "@/lib/mongo";
import { hashPassword, passwordIssues } from "@/lib/security";
const schema = z.object({ token: z.string().min(1), new_password: z.string(), confirm_password: z.string() });
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ detail: "Invalid reset request" }, { status: 400 });
  if (parsed.data.new_password !== parsed.data.confirm_password) return NextResponse.json({ detail: "Passwords do not match" }, { status: 400 });
  const issues = passwordIssues(parsed.data.new_password);
  if (issues.length) return NextResponse.json({ detail: { error: "Password is not strong enough", issues } }, { status: 400 });
  const hash = crypto.createHash("sha256").update(parsed.data.token).digest("hex");
  const db = await getDb();
  const record = await db.collection<any>("passwordResetTokens").findOne({ token_hash: hash, used: false, expires_at: { $gt: new Date() } });
  if (!record) return NextResponse.json({ detail: "Invalid or expired reset token" }, { status: 400 });
  await db.collection("userGoals").updateOne({ email: record.email }, { $set: { password: await hashPassword(parsed.data.new_password), password_reset_at: new Date().toISOString() } });
  await db.collection("passwordResetTokens").updateOne({ _id: record._id }, { $set: { used: true, used_at: new Date() } });
  return NextResponse.json({ success: true, message: "Password has been reset successfully. You can now log in with your new password." });
}
