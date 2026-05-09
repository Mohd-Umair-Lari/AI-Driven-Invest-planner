const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

// Backend URLs


const DEV_URL = "http://localhost:5000";
// Connected to your Hugging Face Backend URL
const PRODUCTION_URL = "https://umairlari-ai-financial-advisor-backend.hf.space";
// const PRODUCTION_URL = "https://ai-driven-invest-planner.onrender.com"
// Connection url to the Render backend

export const BACKEND_URL = isDev ? DEV_URL : PRODUCTION_URL;

console.log("🔗 Backend URL:", BACKEND_URL);
console.log(`📍 Environment: ${isDev ? "DEVELOPMENT" : "PRODUCTION"}`);
