

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


export function setupChatbot() {
  
  const deleteBtn = document.getElementById('chat-delete-btn');
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

  const chatInput = document.getElementById('ai-chat-input');
  const chatSend = document.getElementById('ai-chat-send');
  const chatMessages = document.getElementById('ai-chat-messages');
  const sessionsList = document.getElementById('chat-sessions-list');
  const newChatBtn = document.getElementById('chat-new-btn');

  if (!chatInput || !chatSend || !chatMessages) return;

  let activeSessionId = null;
  let sessionsCache = [];

  function scrollChat() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showEmptyHint() {
    chatMessages.innerHTML = `
      <p class="chat-empty-hint">
        <strong>FinPass AI is ready</strong>
        Ask about savings, SIPs, goals, or your spending.<br>
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

  function renderSessionsList() {
    if (!sessionsList) return;
    if (!sessionsCache.length) {
      sessionsList.innerHTML = '<p class="chat-sessions-empty text-xs text-slate-400 p-2">No chats yet</p>';
      return;
    }
    sessionsList.innerHTML = sessionsCache.map((s) => {
      const active = s.session_id === activeSessionId ? ' active' : '';
      const title = escapeHtml(s.title || 'Conversation');
      return `<button type="button" class="chat-session-item${active}" data-session-id="${escapeHtml(s.session_id)}" title="${title}">${title}</button>`;
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
    } else {
      activeSessionId = newChatSessionId();
      persistActiveSession(user.email);
      showEmptyHint();
    }
  }

  const handleSend = async () => {
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

  chatSend.addEventListener('click', handleSend);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewConversation);
  }

  window.__initAdvisorChat = initChatForUser;
  showEmptyHint();
  console.log("🤖 Chatbot setup complete");
}
