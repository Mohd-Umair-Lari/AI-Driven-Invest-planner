

import { apiFetch } from "../api.js";
import { escapeHtml } from "../utils/formatting.js";
import { newChatSessionId, chatStorageKey } from "../utils/chat-session.js";

let currentUserRef = null;


export function setChatbotUser(user) {
  currentUserRef = user;
}


function formatAiText(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul class="chat-list">$1</ul>')
    .replace(/\n/g, '<br>');
}


export function setupChatbot(options = {}) {
  const scope = options.scope || document;
  const readOnly = options.readOnly === true;
  const exposeGlobal = options.exposeGlobal !== false;

  const deleteBtn = scope.querySelector('#chat-delete-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      if (!activeSessionId) {
        alert('No conversation selected to delete.');
        return;
      }
      const user = currentUserRef || JSON.parse(localStorage.getItem('user') || '{}');
      if (!user?.email) {
        alert('User not logged in.');
        return;
      }
      if (!confirm('Delete this conversation? This cannot be undone.')) return;
      try {
        await apiFetch(`/api/chat/history/${encodeURIComponent(user.email)}/${encodeURIComponent(activeSessionId)}`, { method: 'DELETE' });
        sessionsCache = sessionsCache.filter(s => s.session_id !== activeSessionId);
        activeSessionId = null;
        renderSessionsList();
        showEmptyHint();
      } catch (err) {
        console.error('Failed to delete chat session:', err);
        alert('Could not delete the conversation.');
      }
    });
  }

  const chatInput = scope.querySelector('#ai-chat-input');
  const chatSend = scope.querySelector('#ai-chat-send');
  const chatMessages = scope.querySelector('#ai-chat-messages');
  const sessionsList = scope.querySelector('#chat-sessions-list');
  const newChatBtn = scope.querySelector('#chat-new-btn');

  if (!chatMessages) return null;

  let activeSessionId = null;
  let sessionsCache = [];
  const interactive = Boolean(chatInput && chatSend && !readOnly);

  function scrollChat() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showEmptyHint() {
    const emptyText = readOnly
      ? 'Pick a past conversation on the left to review the thread.'
      : 'Ask about savings, SIPs, goals, or your spending.';
    chatMessages.innerHTML = `
      <p class="chat-empty-hint">
        <strong>FinPass AI is ready</strong>
        ${emptyText}<br>
        Your conversations are saved — pick one on the left to continue.
      </p>`;
  }

  function appendUserMsg(text) {
    const div = document.createElement('div');
    div.className = 'chat-user-msg';
    div.innerHTML = `<div class="chat-user-bubble"><p class="chat-user-text">${escapeHtml(text)}</p></div>`;
    chatMessages.appendChild(div);
    scrollChat();
  }

  function appendAiMsg(text) {
    const div = document.createElement('div');
    div.className = 'ai-chat-card';
    div.innerHTML = `
      <div class="ai-msg-icon">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        </svg>
      </div>
      <div class="chat-bubble-ai"><p class="chat-ai-text">${formatAiText(text)}</p></div>`;
    chatMessages.appendChild(div);
    scrollChat();
  }

  function appendError(msg) {
    const div = document.createElement('div');
    div.className = 'ai-chat-card';
    div.innerHTML = `
      <div class="ai-msg-icon" style="background:linear-gradient(135deg,#ef4444,#dc2626)">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      </div>
      <div class="chat-bubble-ai"><p class="chat-ai-text" style="color:#ef4444;">⚠️ ${escapeHtml(msg)}</p></div>`;
    chatMessages.appendChild(div);
    scrollChat();
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'ai-chat-card';
    div.id = 'chat-typing-indicator';
    div.innerHTML = `
      <div class="ai-msg-icon">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        </svg>
      </div>
      <div class="chat-bubble-ai chat-typing"><span></span><span></span><span></span></div>`;
    chatMessages.appendChild(div);
    scrollChat();
    return div;
  }

  function renderMessages(messages) {
    chatMessages.innerHTML = '';
    if (!messages?.length) {
      showEmptyHint();
      return;
    }
    for (const m of messages) {
      if (m.role === 'user') appendUserMsg(m.content);
      else if (m.role === 'assistant') appendAiMsg(m.content);
    }
  }

  function persistActiveSession(email) {
    if (email && activeSessionId) {
      localStorage.setItem(chatStorageKey(email), activeSessionId);
    }
  }

  function formatSessionTime(value) {
    if (!value) return 'Just now';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Recent';
    const now = Date.now();
    const diffMinutes = Math.floor((now - date.getTime()) / 60000);
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  }

  function formatMessageCount(count) {
    const safeCount = Number.isFinite(Number(count)) ? Number(count) : 0;
    return `${safeCount} message${safeCount === 1 ? '' : 's'}`;
  }

  function renderSessionsList() {
    if (!sessionsList) return;
    if (!sessionsCache.length) {
      sessionsList.innerHTML = `
        <div class="chat-sessions-empty">
          <p class="chat-sessions-empty-title">No chats yet</p>
          <p class="chat-sessions-empty-sub">Start a new chat to save your first conversation.</p>
        </div>`;
      return;
    }
    sessionsList.innerHTML = sessionsCache.map((s) => {
      const active = s.session_id === activeSessionId ? ' active' : '';
      const title = escapeHtml(s.title || 'Conversation');
      const preview = escapeHtml((s.preview || 'No messages yet').trim());
      const updated = formatSessionTime(s.updated_at || s.created_at);
      const count = formatMessageCount(s.message_count);
      return `
        <button type="button" class="chat-session-item${active}" data-session-id="${escapeHtml(s.session_id)}" title="${title}">
          <span class="chat-session-title">${title}</span>
          <span class="chat-session-preview">${preview}</span>
          <span class="chat-session-meta">
            <span class="chat-session-time">${escapeHtml(updated)}</span>
            <span class="chat-session-count">${escapeHtml(count)}</span>
          </span>
        </button>`;
    }).join('');

    sessionsList.querySelectorAll('.chat-session-item').forEach((btn) => {
      btn.addEventListener('click', () => resumeSession(btn.dataset.sessionId));
    });
  }

  async function fetchSessions(email) {
    try {
      const data = await apiFetch(`/api/chat/sessions/${encodeURIComponent(email)}`);
      sessionsCache = data.sessions || [];
      renderSessionsList();
    } catch (err) {
      console.warn('Could not load chat sessions:', err.message);
      if (sessionsList) {
        sessionsList.innerHTML = '<p class="chat-sessions-empty text-xs text-slate-400 p-2">Unavailable</p>';
      }
    }
  }

  async function resumeSession(sessionId) {
    const user = currentUserRef || JSON.parse(localStorage.getItem('user') || '{}');
    if (!user?.email || !sessionId) return;

    activeSessionId = sessionId;
    persistActiveSession(user.email);
    renderSessionsList();

    try {
      const data = await apiFetch(
        `/api/chat/history/${encodeURIComponent(user.email)}/${encodeURIComponent(sessionId)}`
      );
      renderMessages(data.messages || []);
    } catch (err) {
      showEmptyHint();
      appendError('Could not load this conversation.');
    }
  }

  function startNewConversation() {
    const user = currentUserRef || JSON.parse(localStorage.getItem('user') || '{}');
    if (!user?.email) return;

    activeSessionId = newChatSessionId();
    persistActiveSession(user.email);
    showEmptyHint();
    renderSessionsList();
    chatInput.focus();
  }

  async function initChatForUser(user) {
    if (!user?.email) {
      showEmptyHint();
      return;
    }

    await fetchSessions(user.email);

    const saved = localStorage.getItem(chatStorageKey(user.email));
    const savedExists = saved && sessionsCache.some((s) => s.session_id === saved);

    if (savedExists) {
      await resumeSession(saved);
    } else if (sessionsCache.length > 0) {
      await resumeSession(sessionsCache[0].session_id);
    } else if (interactive) {
      activeSessionId = newChatSessionId();
      persistActiveSession(user.email);
      showEmptyHint();
    } else {
      activeSessionId = null;
      showEmptyHint();
    }
  }

  const handleSend = async () => {
    if (!interactive) return;
    const text = chatInput.value.trim();
    if (!text) return;

    const user = currentUserRef || JSON.parse(localStorage.getItem('user') || '{}');
    if (!user?.email) {
      appendError('Please log in to use the AI advisor.');
      return;
    }

    if (!activeSessionId) {
      activeSessionId = newChatSessionId();
      persistActiveSession(user.email);
    }

    const hint = chatMessages.querySelector('.chat-empty-hint');
    if (hint) hint.remove();

    chatInput.value = '';
    chatInput.disabled = true;
    chatSend.disabled = true;

    appendUserMsg(text);
    const typingEl = showTyping();

    try {
      const res = await apiFetch('/api/advisor/chat', {
        method: 'POST',
        body: JSON.stringify({
          email: user.email,
          question: text,
          session_id: activeSessionId,
          context: {
            monthly_income: user.financials?.['monthly-income'] || 0,
            monthly_expenses: user.financials?.['monthly-expenses'] || 0,
            debt: user.financials?.debt || 0,
            risk_appetite: user.investments?.['risk-opt'] || 'moderate',
          },
        }),
      });

      typingEl.remove();
      if (res.session_id) {
        activeSessionId = res.session_id;
        persistActiveSession(user.email);
      }
      appendAiMsg(res.response || 'Sorry, I did not get a response. Please try again.');
      await fetchSessions(user.email);
      renderSessionsList();

    } catch (err) {
      typingEl.remove();
      if (err.message?.includes('401')) {
        appendError('Session expired. Please log in again.');
      } else if (err.message?.includes('timeout') || err.name === 'AbortError') {
        appendError('The request timed out. Please try again in a moment.');
      } else {
        appendError(err.message || 'Something went wrong.');
      }
    } finally {
      chatInput.disabled = false;
      chatSend.disabled = false;
      chatInput.focus();
    }
  };

  if (interactive) {
    chatSend.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewConversation);
  }

  if (exposeGlobal) {
    window.__initAdvisorChat = initChatForUser;
  }
  showEmptyHint();
  console.log("🤖 Chatbot setup complete");
  return initChatForUser;
}
