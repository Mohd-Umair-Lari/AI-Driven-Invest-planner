/**
 * Standalone AI Advisor page chatbot.
 * Uses the AdvisorChatbot class to render a full chat UI inside a container.
 */

import { apiFetch } from "./api.js";
import { escapeHtml } from "./utils/formatting.js";
import { newChatSessionId, chatStorageKey } from "./utils/chat-session.js";

export class AdvisorChatbot {
  constructor() {
    this.messageContainer = null;
    this.inputField = null;
    this.sendButton = null;
    this.sessionsListEl = null;
    this.newChatBtn = null;
    this.currentUser = null;
    this.activeSessionId = null;
    this.sessionsCache = [];
    this.isLoading = false;
  }

  init(containerId = "advisor-chat-container") {
    this.messageContainer = document.getElementById(containerId);
    if (!this.messageContainer) {
      console.warn("Advisor chatbot container not found");
      return false;
    }

    const userStr = localStorage.getItem("user");
    if (userStr) {
      this.currentUser = JSON.parse(userStr);
    }

    this.setupUI();
    this.attachEventListeners();
    if (this.currentUser?.email) {
      this.bootstrap();
    }
    return true;
  }

  setupUI() {
    this.messageContainer.innerHTML = `
      <div class="flex flex-col h-full bg-white dark:bg-slate-800 rounded-xl shadow-lg transition-colors min-h-[400px]">
        <div class="bg-gradient-to-r from-indigo-500 to-violet-600 p-4 rounded-t-xl text-white flex justify-between items-center">
          <div>
            <h3 class="font-bold flex items-center gap-2">AI Financial Advisor</h3>
            <p class="text-xs text-white/80 mt-1">Conversations saved · resume anytime</p>
          </div>
          <button type="button" id="advisor-new-chat" class="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg">+ New</button>
        </div>
        <div class="flex flex-1 min-h-0">
          <aside class="w-28 border-r border-slate-200 dark:border-slate-700 p-2 flex flex-col">
            <p class="text-[10px] font-bold uppercase text-slate-400 mb-2">Chats</p>
            <div id="advisor-sessions-list" class="flex-1 overflow-y-auto text-xs"></div>
          </aside>
          <div class="flex flex-col flex-1 min-w-0">
            <div id="advisor-messages" class="flex-1 overflow-y-auto p-4 space-y-3"></div>
            <div class="border-t border-slate-200 dark:border-slate-700 p-4">
              <div class="flex gap-3">
                <input id="advisor-input" type="text" placeholder="Message FinPass AI…" class="flex-1 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white" />
                <button id="advisor-send" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg font-semibold disabled:opacity-50">Send</button>
              </div>
            </div>
          </div>
        </div>
      </div>`;

    this.inputField = document.getElementById("advisor-input");
    this.sendButton = document.getElementById("advisor-send");
    this.sessionsListEl = document.getElementById("advisor-sessions-list");
    this.newChatBtn = document.getElementById("advisor-new-chat");
    this.showEmptyHint();
  }

  attachEventListeners() {
    this.sendButton?.addEventListener("click", () => this.sendMessage());
    this.newChatBtn?.addEventListener("click", () => this.startNewConversation());
    this.inputField?.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  async bootstrap() {
    await this.fetchSessions();
    const saved = localStorage.getItem(chatStorageKey(this.currentUser.email));
    const exists = saved && this.sessionsCache.some((s) => s.session_id === saved);
    if (exists) await this.resumeSession(saved);
    else if (this.sessionsCache.length) await this.resumeSession(this.sessionsCache[0].session_id);
    else this.startNewConversation();
  }

  showEmptyHint() {
    const el = document.getElementById("advisor-messages");
    if (!el) return;
    el.innerHTML = `<p class="text-sm text-slate-400 text-center py-8">Ask about your finances. Pick a past chat on the left to continue.</p>`;
  }

  renderSessionsList() {
    if (!this.sessionsListEl) return;
    if (!this.sessionsCache.length) {
      this.sessionsListEl.innerHTML = `<p class="text-slate-400 p-1">None yet</p>`;
      return;
    }
    this.sessionsListEl.innerHTML = this.sessionsCache
      .map((s) => {
        const active = s.session_id === this.activeSessionId ? " font-bold text-indigo-600" : " text-slate-500";
        return `<button type="button" data-sid="${escapeHtml(s.session_id)}" class="block w-full text-left p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-700${active}">${escapeHtml(s.title || "Chat")}</button>`;
      })
      .join("");
    this.sessionsListEl.querySelectorAll("button[data-sid]").forEach((btn) => {
      btn.addEventListener("click", () => this.resumeSession(btn.dataset.sid));
    });
  }

  async fetchSessions() {
    try {
      const data = await apiFetch(`/api/chat/sessions/${encodeURIComponent(this.currentUser.email)}`);
      this.sessionsCache = data.sessions || [];
      this.renderSessionsList();
    } catch {
      /* ignore */
    }
  }

  async resumeSession(sessionId) {
    this.activeSessionId = sessionId;
    localStorage.setItem(chatStorageKey(this.currentUser.email), sessionId);
    this.renderSessionsList();
    try {
      const data = await apiFetch(
        `/api/chat/history/${encodeURIComponent(this.currentUser.email)}/${encodeURIComponent(sessionId)}`
      );
      this.renderMessages(data.messages || []);
    } catch {
      this.showEmptyHint();
    }
  }

  startNewConversation() {
    this.activeSessionId = newChatSessionId();
    localStorage.setItem(chatStorageKey(this.currentUser.email), this.activeSessionId);
    this.showEmptyHint();
    this.renderSessionsList();
    this.inputField?.focus();
  }

  renderMessages(messages) {
    const el = document.getElementById("advisor-messages");
    if (!el) return;
    el.innerHTML = "";
    if (!messages.length) {
      this.showEmptyHint();
      return;
    }
    for (const m of messages) {
      this.addMessage(m.role === "user" ? "user" : "advisor", m.content, false);
    }
  }

  async sendMessage() {
    const message = this.inputField?.value?.trim();
    if (!message || this.isLoading) return;
    if (!this.currentUser?.email) {
      this.addMessage("system", "Please log in to use the advisor.");
      return;
    }
    if (!this.activeSessionId) this.startNewConversation();

    const hint = document.querySelector("#advisor-messages .text-slate-400");
    if (hint?.closest("#advisor-messages") && hint.textContent.includes("Ask about")) {
      document.getElementById("advisor-messages").innerHTML = "";
    }

    this.addMessage("user", message);
    this.inputField.value = "";
    this.setLoading(true);

    try {
      const res = await apiFetch("/api/advisor/chat", {
        method: "POST",
        body: JSON.stringify({
          question: message,
          email: this.currentUser.email,
          session_id: this.activeSessionId,
          context: {
            monthly_income: this.currentUser.financials?.["monthly-income"] || 0,
            monthly_expenses: this.currentUser.financials?.["monthly-expenses"] || 0,
            total_savings: this.currentUser.financials?.["total-savings"] || 0,
            debt: this.currentUser.financials?.debt || 0,
            risk_appetite: this.currentUser["Risk-Appetite"] || "Moderate",
          },
        }),
      });

      if (res.session_id) {
        this.activeSessionId = res.session_id;
        localStorage.setItem(chatStorageKey(this.currentUser.email), res.session_id);
      }
      this.addMessage("advisor", res.response || "No response.");
      await this.fetchSessions();
    } catch (error) {
      this.addMessage("system", error.message || "Request failed.");
    } finally {
      this.setLoading(false);
    }
  }

  addMessage(sender, text, scroll = true) {
    const messagesDiv = document.getElementById("advisor-messages");
    if (!messagesDiv) return;

    const messageEl = document.createElement("div");
    messageEl.className = "flex gap-3";

    if (sender === "user") {
      messageEl.className = "flex justify-end";
      messageEl.innerHTML = `<p class="text-sm bg-indigo-600 text-white rounded-lg px-4 py-2 max-w-[85%]">${escapeHtml(text)}</p>`;
    } else if (sender === "advisor") {
      messageEl.innerHTML = `<div class="text-sm bg-slate-100 dark:bg-slate-700 rounded-lg px-4 py-2 max-w-[90%] whitespace-pre-wrap">${escapeHtml(text)}</div>`;
    } else {
      messageEl.innerHTML = `<p class="text-xs text-center text-slate-400 w-full">${escapeHtml(text)}</p>`;
    }

    messagesDiv.appendChild(messageEl);
    if (scroll) messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  setLoading(isLoading) {
    this.isLoading = isLoading;
    if (this.sendButton) this.sendButton.disabled = isLoading;
    if (this.inputField) this.inputField.disabled = isLoading;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new AdvisorChatbot().init());
} else {
  new AdvisorChatbot().init();
}
