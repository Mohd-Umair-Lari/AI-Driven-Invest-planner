

import { apiFetch } from "./api.js";
import { setupNavigation, toggleSidebar } from "./components/navigation.js";
import { populateMetrics, populateGoalData, loadRecommendedActions } from "./components/metrics.js";
import { setupChatbot, setChatbotUser } from "./components/chatbot.js";
import { populateProfileData, setupProfileEditor } from "./components/profile.js";

console.log("📊 Dashboard Initializing...");

let currentUser = null;


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


window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/';
  }
};


window.toggleSidebar = toggleSidebar;


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