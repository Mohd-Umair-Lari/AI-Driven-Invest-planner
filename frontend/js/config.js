// For local development: http://localhost:5000
// For production: Update the production URL below or use environment variables

const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

export const BACKEND_URL = isDev 
  ? "http://localhost:5000"
  : "https://ai-driven-invest-planner.onrender.com";