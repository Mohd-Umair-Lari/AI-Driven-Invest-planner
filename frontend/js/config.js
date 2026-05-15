const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const DEV_URL = "http://localhost:5000";

const PRODUCTION_URL = "https://umairlari-ai-financial-advisor-backend.hf.space"

export const BACKEND_URL = isDev ? DEV_URL : PRODUCTION_URL;

console.log("🔗 Backend URL:", BACKEND_URL);
console.log(`📍 Environment: ${isDev ? "DEVELOPMENT" : "PRODUCTION"}`);
