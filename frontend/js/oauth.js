// Shared OAuth button wiring for both sign-in and sign-up pages.
//
// Sign in and sign up are the SAME OAuth flow: the backend upserts the user,
// so an existing account logs in and a new one is created — no separate paths.
//
// Also fixes the "stuck spinner" bug: when the user backs out of the provider's
// consent screen, the browser restores this page from its back/forward cache
// (bfcache) with the button still showing "Connecting…". We reset every button
// on `pageshow` so it never keeps spinning.

const BACKEND_URL = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "http://localhost:5000"
  : "https://umairlari-ai-financial-advisor-backend.hf.space";

const SPINNER = `<svg class="animate-spin h-5 w-5 text-slate-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Connecting...`;

// provider -> button element id
const PROVIDERS = {
  github: "oauth-btn",
  google: "google-oauth-btn",
};

export function initOAuthButtons() {
  const buttons = [];

  for (const [provider, id] of Object.entries(PROVIDERS)) {
    const btn = document.getElementById(id);
    if (!btn) continue;

    // Remember the original label so we can restore it after a cancel.
    const originalHTML = btn.innerHTML;
    buttons.push({ btn, originalHTML });

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      if (btn.dataset.busy === "1") return; // guard against double clicks
      btn.dataset.busy = "1";
      btn.disabled = true;
      btn.innerHTML = SPINNER;
      window.location.href = `${BACKEND_URL}/api/auth/${provider}/authorize`;
    });
  }

  // When the user hits Back from the provider, the page is often restored from
  // bfcache with the spinner frozen. Reset every button to its idle state.
  const reset = () => {
    for (const { btn, originalHTML } of buttons) {
      btn.dataset.busy = "0";
      btn.disabled = false;
      btn.innerHTML = originalHTML;
    }
  };
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) reset();
  });
  window.addEventListener("pagehide", () => {});
}
