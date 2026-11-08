import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { callbackUrl, createOauthState } from "@/lib/oauth";
export async function GET() {
  if (!env.googleClientId) return NextResponse.json({ detail: "Google OAuth is not configured" }, { status: 503 });
  const state = await createOauthState("google"); const url = new URL("https://accounts.google.com/o/oauth2/v2/auth"); url.searchParams.set("client_id", env.googleClientId); url.searchParams.set("redirect_uri", callbackUrl("google")); url.searchParams.set("response_type", "code"); url.searchParams.set("scope", "openid email profile"); url.searchParams.set("state", state); url.searchParams.set("access_type", "online"); url.searchParams.set("prompt", "select_account"); return NextResponse.redirect(url);
}
