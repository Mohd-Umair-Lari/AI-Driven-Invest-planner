import { NextResponse } from "next/server";
import { z } from "zod";
import crypto from "node:crypto";
import { getDb } from "@/lib/mongo";
const schema = z.object({ token: z.string().min(1) });
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ detail: "Token is required" }, { status: 400 });
  const hash = crypto.createHash("sha256").update(parsed.data.token).digest("hex");
  const record = await (await getDb()).collection<any>("passwordResetTokens").findOne({ token_hash: hash, used: false, expires_at: { $gt: new Date() } });
  if (!record) return NextResponse.json({ detail: "Invalid or expired reset token" }, { status: 400 });
  return NextResponse.json({ success: true, email: record.email, message: "Token is valid. You can now reset your password." });
}
