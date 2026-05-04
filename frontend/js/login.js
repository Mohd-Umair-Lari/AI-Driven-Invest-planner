import { apiFetch } from "./api.js";

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
    const password = document.getElementById("login-password")?.value.trim();

    try {
      const res = await apiFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      localStorage.setItem("user", JSON.stringify(res.user));
      window.location.href = "./dashboard.html";

    } catch (err) {
      console.error("Login failed:", err);
      alert(err.message || "Login failed");
    }
  });

  const oauthBtn = document.getElementById("oauth-btn");
  if (oauthBtn) {
    oauthBtn.addEventListener("click", (e) => {
      e.preventDefault();
      // Mock OAuth Flow for Demonstration
      // In production, integrate Firebase Auth or Google Identity Services
      oauthBtn.innerHTML = `<svg class="animate-spin h-5 w-5 text-slate-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Connecting...`;
      
      setTimeout(() => {
        const mockOAuthUser = {
          email: "demo.oauth@example.com",
          Name: "Demo User",
          onboarding: { status: "not_started" }
        };
        localStorage.setItem("user", JSON.stringify(mockOAuthUser));
        window.location.href = "./dashboard.html";
      }, 1500);
    });
  }
});