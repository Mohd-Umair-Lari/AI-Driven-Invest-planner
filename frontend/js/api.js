import { BACKEND_URL } from "./config.js";

export async function fetchInsights(financialState) {
  return await apiFetch("/api/intelligence/insights", {
    method: "POST",
    body: JSON.stringify(financialState)
  });
}

export async function apiFetch(endpoint, options = {}) {
  try {
    const url = `${BACKEND_URL}${endpoint}`;
    console.log(`📡 API Call: ${options.method || 'GET'} ${url}`);
    
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options,
      timeout: 15000
    });

    const data = await res.json().catch(() => ({}));
    
    if (!res.ok) {
      console.error(`❌ API Error [${res.status}]:`, data.message || res.statusText);
      throw new Error(data.message || `HTTP ${res.status}: ${res.statusText}`);
    }
    
    console.log(`✅ API Success: ${endpoint}`);
    return data;
  } catch (err) {
    console.error(`🔥 API Exception:`, err.message);
    throw err;
  }
}

