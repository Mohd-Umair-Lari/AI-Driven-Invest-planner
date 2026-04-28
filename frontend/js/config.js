// Production URL configuration
const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

// Backend URLs
const DEV_URL = "http://localhost:5000";
// 🔴 CHANGE THIS to your Railway backend URL: https://your-railway-project.railway.app
const PRODUCTION_URL = "https://ai-driven-invest-planner.onrender.com"; // ← Update this after creating Railway project

export const BACKEND_URL = isDev ? DEV_URL : PRODUCTION_URL;

console.log("🔗 Backend URL:", BACKEND_URL);
console.log(`📍 Environment: ${isDev ? "DEVELOPMENT" : "PRODUCTION"}`);
