import { NextResponse } from "next/server";
import { z } from "zod";
import { getDb, stripMongoId } from "@/lib/mongo";
import { createToken } from "@/lib/jwt";
import { hashPassword, passwordIssues } from "@/lib/security";

const schema = z.object({
  Name: z.string().min(1), email: z.string().email(), password: z.string().min(1),
  Age: z.string().optional().default(""), "employment-status": z.string().optional().default("Salaried"),
  Goal: z.record(z.string(), z.unknown()).optional().default({}), financials: z.record(z.string(), z.unknown()).optional().default({}),
  investments: z.record(z.string(), z.unknown()).optional().default({}), progress: z.record(z.string(), z.unknown()).optional().default({}),
});

export async function POST(request: Request) {
  try {
    const body = schema.parse(await request.json()); const issues = passwordIssues(body.password);
    if (issues.length) return NextResponse.json({ detail: { error: "Password is not strong enough", issues } }, { status: 400 });
    const email = body.email.toLowerCase(); const users = (await getDb()).collection("userGoals");
    if (await users.findOne({ email })) return NextResponse.json({ detail: "Email already registered" }, { status: 409 });
    const user = { Name: body.Name, email, password: await hashPassword(body.password), Age: body.Age, "employment-status": body["employment-status"], Goal: body.Goal, financials: body.financials, investments: body.investments, progress: body.progress, onboarding: { status: "in_progress", current_step: 0, last_updated: new Date().toISOString() }, created_at: new Date().toISOString(), security_version: 1 };
    const result = await users.insertOne(user); const id = String(result.insertedId);
    return NextResponse.json({ status: "success", user: stripMongoId({ ...user, _id: result.insertedId }), access_token: await createToken(email, id, "access"), refresh_token: await createToken(email, id, "refresh"), token_type: "bearer", expires_in: 900 }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) return NextResponse.json({ detail: error.issues }, { status: 422 });
    console.error("Signup error", error); return NextResponse.json({ detail: "Signup failed" }, { status: 500 });
  }
}
