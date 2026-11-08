import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { callbackUrl, createOauthState } from "@/lib/oauth";
export async function GET() {
  if (!env.githubClientId) return NextResponse.json({ detail: "GitHub OAuth is not configured" }, { status: 503 });
  const state = await createOauthState("github"); const url = new URL("https://github.com/login/oauth/authorize"); url.searchParams.set("client_id", env.githubClientId); url.searchParams.set("redirect_uri", callbackUrl("github")); url.searchParams.set("scope", "read:user user:email"); url.searchParams.set("state", state); url.searchParams.set("allow_signup", "true"); return NextResponse.redirect(url);
}
