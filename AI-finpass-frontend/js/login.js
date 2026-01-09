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

    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    try {
      const res = await apiFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      localStorage.setItem("user", JSON.stringify(res.user));
      window.location.href = "/dashboard.html";

    } catch (err) {
      console.error("Login failed:", err);
      alert(err.message || "Login failed");
    }
  });
});