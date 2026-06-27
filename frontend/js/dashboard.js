/**
 * Dashboard — Main orchestrator.
 *
 * Loads user data, then delegates to component modules for
 * navigation, metrics, chatbot, and profile functionality.
 */

import { apiFetch } from "./api.js";
import { setupNavigation, toggleSidebar } from "./components/navigation.js";
import { populateMetrics, populateGoalData, loadRecommendedActions } from "./components/metrics.js";
import { setupChatbot, setChatbotUser } from "./components/chatbot.js";
import { populateProfileData, setupProfileEditor } from "./components/profile.js";

console.log("📊 Dashboard Initializing...");

let currentUser = null;

/**
 * Load the current user from localStorage, redirecting if not logged in.
 * Auto-seeds test data if the user has no financials.
 */
async function loadUserData() {
  let user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    window.location.href = "/static/login.html";
    return null;
  }

  if (!user.financials || Object.keys(user.financials).length === 0) {
    try {
      console.log("📝 Initializing test data...");
      const response = await apiFetch(`/api/init-test-data/${user.email}`, { method: "POST" });
      user = response.user;
      localStorage.setItem("user", JSON.stringify(user));
      console.log("✅ Test data initialized");
    } catch (err) {
      console.warn("⚠️ Test data init failed:", err.message);
    }
  }

  currentUser = user;
  console.log("👤 User loaded:", user.Name);
  return user;
}

/**
 * Logout: clear storage and redirect.
 */
window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/';
  }
};

/**
 * Mobile sidebar toggle (exposed globally for onclick handler).
 */
window.toggleSidebar = toggleSidebar;

/**
 * Bootstrap the dashboard on page load.
 */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    setupNavigation(populateProfileData);
    setupProfileEditor();
    setupChatbot();

    const user = await loadUserData();
    if (!user) return;

    setChatbotUser(user);

    if (typeof window.__initAdvisorChat === 'function') {
      await window.__initAdvisorChat(user);
    }

    populateMetrics(user);
    await Promise.all([
      populateGoalData(user),
      loadRecommendedActions(user),
    ]);

    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});