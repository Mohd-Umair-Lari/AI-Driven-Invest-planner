export const env = {
  mongoUri: process.env.MONGO_URI ?? "",
  dbName: process.env.DB_NAME ?? "mockDB",
  jwtSecret: process.env.JWT_SECRET ?? "",
  groqApiKey: process.env.GROQ_API_KEY ?? "",
  groqModel: process.env.GROQ_MODEL ?? "openai/gpt-oss-120b",
  resendApiKey: process.env.RESEND_API_KEY ?? "",
  appUrl: process.env.APP_URL ?? "http://localhost:3000",
  githubClientId: process.env.GITHUB_CLIENT_ID ?? "",
  githubClientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
  googleClientId: process.env.GOOGLE_CLIENT_ID ?? "",
  googleClientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
};

export function requireEnv(value: string, name: string): string {
  if (!value) throw new Error(`${name} is not configured`);
  return value;
}
