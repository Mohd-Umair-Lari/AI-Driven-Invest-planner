

import { apiFetch } from "./api.js";
import { setupNavigation, toggleSidebar } from "./components/navigation.js";
import { populateMetrics, populateGoalData, loadRecommendedActions } from "./components/metrics.js";
import { setupChatbot, setChatbotUser } from "./components/chatbot.js";
import { populateProfileData, setupProfileEditor } from "./components/profile.js";
import { chatStorageKey } from "./utils/chat-session.js";

console.log("📊 Dashboard Initializing...");

let currentUser = null;
let initDashboardChat = null;
let initModalChat = null;
let modalInitialized = false;

function openChatModal() {
  const modal = document.getElementById('chatbot-modal');
  if (!modal) return;
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.classList.add('chatbot-modal-open');
}

async function openChatModalWithNewChat() {
  openChatModal();
  if (!modalInitialized && typeof initModalChat === 'function' && currentUser) {
    await initModalChat(currentUser);
    modalInitialized = true;
  }
  document.getElementById('chat-new-btn')?.click();
}

async function openChatModalForSession(sessionId) {
  if (currentUser?.email && sessionId) {
    localStorage.setItem(chatStorageKey(currentUser.email), sessionId);
  }
  openChatModal();
  if (!modalInitialized && typeof initModalChat === 'function' && currentUser) {
    await initModalChat(currentUser);
    modalInitialized = true;
  }
}

function closeChatModal() {
  const modal = document.getElementById('chatbot-modal');
  if (!modal) return;
  modal.classList.remove('is-open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('chatbot-modal-open');
}


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
    const dashboardChatRoot = document.getElementById('dashboard-chat-panel');
    const modalChatRoot = document.getElementById('chatbot-modal-shell');
    initDashboardChat = setupChatbot({
      scope: dashboardChatRoot,
      readOnly: true,
      historyOnly: true,
      exposeGlobal: false,
      onSessionSelected: openChatModalForSession,
    });
    initModalChat = setupChatbot({ scope: modalChatRoot, readOnly: false, exposeGlobal: false });

    const launchBtn = document.getElementById('chat-launch-btn');
    const closeBtn = document.getElementById('chat-close-btn');
    const backdrop = document.getElementById('chatbot-modal-backdrop');

    launchBtn?.addEventListener('click', openChatModalWithNewChat);
    closeBtn?.addEventListener('click', closeChatModal);
    backdrop?.addEventListener('click', closeChatModal);
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeChatModal();
    });

    const user = await loadUserData();
    if (!user) return;

    setChatbotUser(user);

    if (typeof initDashboardChat === 'function') {
      await initDashboardChat(user);
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