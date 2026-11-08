import { NextResponse } from "next/server";
import { z } from "zod";
import { getDb, stripMongoId } from "@/lib/mongo";
import { createToken } from "@/lib/jwt";
import { verifyPassword } from "@/lib/security";

const schema = z.object({ email: z.string().email(), password: z.string().min(1) });

export async function POST(request: Request) {
  try {
    const body = schema.parse(await request.json());
    const email = body.email.toLowerCase();
    const user = await (await getDb()).collection("userGoals").findOne({ email });
    if (!user || !(await verifyPassword(body.password, String(user.password ?? "")))) return NextResponse.json({ detail: "Invalid credentials" }, { status: 401 });
    const accessToken = await createToken(email, String(user._id), "access");
    const refreshToken = await createToken(email, String(user._id), "refresh");
    return NextResponse.json({ status: "success", user: stripMongoId(user), access_token: accessToken, refresh_token: refreshToken, token_type: "bearer", expires_in: 900 });
  } catch (error) {
    if (error instanceof z.ZodError) return NextResponse.json({ detail: error.issues }, { status: 422 });
    console.error("Login error", error); return NextResponse.json({ detail: "Login failed" }, { status: 500 });
  }
}
