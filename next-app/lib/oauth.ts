import crypto from "node:crypto";
import { getDb, stripMongoId } from "./mongo";
import { createToken } from "./jwt";
import { env, requireEnv } from "./env";

export async function createOauthState(provider: string) {
  const state = crypto.randomBytes(32).toString("base64url");
  await (await getDb()).collection("oauthStates").insertOne({ state, provider, expires_at: new Date(Date.now() + 600000) });
  return state;
}

export async function consumeOauthState(provider: string, state: string) {
  const db = await getDb();
  const record = await db.collection<any>("oauthStates").findOneAndDelete({ state, provider, expires_at: { $gt: new Date() } });
  return Boolean(record);
}

export async function upsertOauthUser(profile: { email: string; name: string; provider: string; providerId: string; login: string; avatarUrl: string }) {
  const db = await getDb(); const now = new Date().toISOString(); const email = profile.email.toLowerCase(); const fields = profile.provider === "github" ? { github_id: profile.providerId, github_login: profile.login } : { google_id: profile.providerId, google_login: profile.login };
  await db.collection("userGoals").updateOne({ email }, { $set: { ...fields, avatar_url: profile.avatarUrl, last_login: now }, $setOnInsert: { Name: profile.name, email, auth_provider: profile.provider, Goal: {}, financials: {}, investments: {}, progress: {}, created_at: now, onboarding: { status: "in_progress", current_step: 0, last_updated: now } } }, { upsert: true });
  const user = await db.collection<any>("userGoals").findOne({ email });
  if (!user) throw new Error("OAuth user could not be created");
  return { user, access_token: await createToken(email, String(user._id), "access"), refresh_token: await createToken(email, String(user._id), "refresh") };
}

export function callbackUrl(provider: string) { return `${requireEnv(env.appUrl, "APP_URL")}/api/auth/${provider}/callback`; }
export function callbackPage() { return `${requireEnv(env.appUrl, "APP_URL")}/static-pages/callback.html`; }
export { stripMongoId };
