// Production URL configuration
const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

// For production Render deployment
const PRODUCTION_URL = "https://ai-driven-invest-planner.onrender.com";
const DEV_URL = "http://localhost:5000";

export const BACKEND_URL = isDev ? DEV_URL : PRODUCTION_URL;

console.log("🔗 Backend URL:", BACKEND_URL);
