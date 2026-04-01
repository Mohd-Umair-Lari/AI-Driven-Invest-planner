import { BACKEND_URL } from "./config.js";

export async function fetchInsights(financialState) {
  return await apiFetch("/api/intelligence/insights", {
    method: "POST",
    body: JSON.stringify(financialState)
  });
}

export async function apiFetch(endpoint, options = {}) {
  const res = await fetch(`${BACKEND_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "API Error");
  return data;
}
