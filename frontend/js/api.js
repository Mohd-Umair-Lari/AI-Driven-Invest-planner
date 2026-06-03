import { BACKEND_URL } from "./config.js";

function formatApiError(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    if (detail.error && Array.isArray(detail.issues)) {
      return `${detail.error}: ${detail.issues.join("; ")}`;
    }
    if (detail.message) return detail.message;
  }
  if (data?.message) return data.message;
  return `HTTP ${status}`;
}

export async function fetchInsights(financialState) {
  return await apiFetch("/api/intelligence/insights", {
    method: "POST",
    body: JSON.stringify(financialState)
  });
}

export async function apiFetch(endpoint, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000);

  try {
    const url = `${BACKEND_URL}${endpoint}`;
    console.log(`📡 API Call: ${options.method || 'GET'} ${url}`);

    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      signal: controller.signal,
      ...options
    });

    clearTimeout(timeoutId);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const message = formatApiError(data, res.status);
      console.error(`❌ API Error [${res.status}]:`, message);
      throw new Error(message);
    }

    console.log(`✅ API Success: ${endpoint}`);
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      console.error(`⏱️ API Timeout: ${endpoint}`);
      throw new Error('Request timed out. The server may be slow — please try again.');
    }
    console.error(`🔥 API Exception:`, err.message);
    throw err;
  }
}

