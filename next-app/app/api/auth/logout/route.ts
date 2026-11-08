import { NextResponse } from "next/server";
import { verifyToken } from "@/lib/jwt";
export async function POST(request: Request) {
  const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "").trim();
  if (!token || !(await verifyToken(token, "access"))) return NextResponse.json({ detail: "Invalid token" }, { status: 401 });
  return NextResponse.json({ message: "Logged out successfully" });
}
