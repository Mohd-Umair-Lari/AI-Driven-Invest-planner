import { apiFetch } from "./api.js";
import { initOAuthButtons } from "./oauth.js";

console.log("🔥 login.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  const loginBtn = document.getElementById("login-btn");

  if (!loginBtn) {
    console.error("Login button not found");
    return;
  }

  loginBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    const email = document.getElementById("login-email")?.value.trim();
    const password = document.getElementById("login-password")?.value ?? "";

    if (!email || !password) {
      alert("Please enter both email and password");
      return;
    }

    try {
      console.log("🔐 Attempting login...");
      const res = await apiFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      if (res.status === "success" && res.user) {
        console.log("✅ Login successful!");
        localStorage.setItem("user", JSON.stringify(res.user));
        if (res.access_token) {
          localStorage.setItem("access_token", res.access_token);
        }
        window.location.href = "./dashboard.html";
      } else {
        throw new Error(res.message || "Login failed - invalid response");
      }

    } catch (err) {
      console.error("❌ Login failed:", err);
      const errorMsg = err.message || "Login failed. Please try again.";

      if (errorMsg.includes("401")) {
        alert("Invalid email or password. Please check and try again.");
      } else if (errorMsg.includes("500")) {
        alert("Server error. Please try again later.");
      } else {
        alert(errorMsg);
      }
    }
  });

  // GitHub + Google OAuth (shared with the sign-up page). Sign in and sign up
  // are the same flow — the backend upserts the account.
  initOAuthButtons();
});