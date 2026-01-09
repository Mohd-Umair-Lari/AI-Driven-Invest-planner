import { apiFetch } from "./api.js";

console.log("🔥 register.js loaded");

const btn = document.getElementById("register-btn");

btn.addEventListener("click", async () => {
  const payload = {
    Name: document.getElementById("name").value.trim(),
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value,
    Age: document.getElementById("age").value,
    "employement-status": document.getElementById("status").value,

    // empty objects – filled later by wizard
    Goal: {},
    financials: {},
    investments: {},
    progress: {}
  };

  if (!payload.Name || !payload.email || !payload.password) {
    alert("Please fill all required fields");
    return;
  }

  try {
    const res = await apiFetch("/api/signup", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    // save user session
    localStorage.setItem("user", JSON.stringify(res.user));

    // go to wizard
    window.location.href = "/wizard.html";

  } catch (err) {
    alert(err.message || "Registration failed");
    console.error(err);
  }
});
