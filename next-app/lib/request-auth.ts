import { NextResponse } from "next/server";
import { verifyToken } from "./jwt";

export async function authorizedEmail(request: Request): Promise<string | NextResponse> {
  const authorization = request.headers.get("authorization");
  const claims = authorization ? await verifyToken(authorization, "access") : null;
  if (!claims?.sub) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  return String(claims.sub).toLowerCase();
}

export function matchesEmail(authenticated: string | NextResponse, requested: string) {
  return authenticated instanceof NextResponse || authenticated === decodeURIComponent(requested).toLowerCase();
}
