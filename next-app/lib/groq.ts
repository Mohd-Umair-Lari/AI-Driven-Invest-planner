import { env, requireEnv } from "./env";

export async function generateResponse(prompt: string) {
  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${requireEnv(env.groqApiKey, "GROQ_API_KEY")}` },
    body: JSON.stringify({ model: env.groqModel, temperature: 0.7, max_tokens: 1024, messages: [{ role: "system", content: "You are FinPass AI, a professional personal finance advisor for Indian investors." }, { role: "user", content: prompt }] }),
  });
  if (!response.ok) throw new Error(`Groq request failed: ${response.status}`);
  const data = await response.json();
  return data.choices?.[0]?.message?.content ?? "No response generated.";
}
