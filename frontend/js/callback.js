// GitHub OAuth callback handler.
// The backend redirects here with tokens in the URL fragment (#access_token=...&refresh_token=...)
// or an error query param (?error=...). We store the session exactly like login.js does.

console.log("🔥 callback.js loaded");

(function handleOAuthCallback() {
  const loading = document.getElementById("cb-loading");
  const errorBox = document.getElementById("cb-error");
  const errorMsg = document.getElementById("cb-error-msg");

  function fail(message) {
    console.error("❌ OAuth callback failed:", message);
    if (loading) loading.classList.add("hidden");
    if (errorBox) errorBox.classList.remove("hidden");
    if (errorMsg) errorMsg.textContent = message;
  }

  // 1. Check for backend-reported error (?error=...)
  const params = new URLSearchParams(window.location.search);
  const error = params.get("error");
  if (error) {
    const friendly = {
      cancelled: "Sign in was cancelled. No account was accessed.",
      access_denied: "Sign in was cancelled. No account was accessed.",
      invalid_state: "Session expired or invalid request. Please try again.",
      token_exchange_failed: "Could not verify your account. Please try again.",
      oauth_error: "The provider reported an error. Please try again.",
      server_error: "Server error during sign in. Please try again later.",
    };
    fail(friendly[error] || decodeURIComponent(error));
    return;
  }

  // 2. Read tokens from the URL fragment (#...)
  const hash = new URLSearchParams(window.location.hash.substring(1));
  const accessToken = hash.get("access_token");
  const refreshToken = hash.get("refresh_token");

  if (!accessToken) {
    fail("No authentication token received. Please try again.");
    return;
  }

  // 3. Fetch the user profile from the backend with the access token.
  //    config.js is not imported (plain script), so determine the URL the same way.
  const isDev = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const backendUrl = isDev
    ? "http://localhost:5000"
    : "https://umairlari-ai-financial-advisor-backend.hf.space";

  fetch(`${backendUrl}/api/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
    .then((res) => {
      if (!res.ok) throw new Error(`Profile fetch failed (HTTP ${res.status})`);
      return res.json();
    })
    .then((profile) => {
      localStorage.setItem("user", JSON.stringify(profile.user || profile));
      localStorage.setItem("access_token", accessToken);
      if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
      // Scrub the tokens from the address bar.
      history.replaceState(null, "", window.location.pathname);

      console.log("✅ GitHub sign in successful");
      const user = JSON.parse(localStorage.getItem("user"));
      if (user && user.onboarding && user.onboarding.status === "completed") {
        window.location.href = "/static/dashboard.html";
      } else {
        window.location.href = "/static/wizard.html";
      }
    })
    .catch((err) => fail(err.message || "Could not load your profile."));
})();
