import { SignJWT, jwtVerify, type JWTPayload } from "jose";
import { env, requireEnv } from "./env";

const secret = () => new TextEncoder().encode(requireEnv(env.jwtSecret, "JWT_SECRET"));

export async function createToken(email: string, userId: string, type: "access" | "refresh") {
  return new SignJWT({ sub: email, user_id: userId, type })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setJti(crypto.randomUUID())
    .setExpirationTime(type === "access" ? "15m" : "7d")
    .sign(secret());
}

export async function verifyToken(token: string, expectedType: "access" | "refresh"): Promise<JWTPayload | null> {
  try {
    const { payload } = await jwtVerify(token.replace(/^Bearer\s+/i, ""), secret());
    return payload.type === expectedType ? payload : null;
  } catch {
    return null;
  }
}
