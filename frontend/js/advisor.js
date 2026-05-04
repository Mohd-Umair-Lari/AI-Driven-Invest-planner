// AI Advisor Chatbot
class AdvisorChatbot {
  constructor() {
    this.messageContainer = null;
    this.inputField = null;
    this.sendButton = null;
    this.currentUser = null;
    this.conversationHistory = [];
    this.isLoading = false;
  }

  init(containerId = 'advisor-chat-container') {
    this.messageContainer = document.getElementById(containerId);
    if (!this.messageContainer) {
      console.warn('Advisor chatbot container not found');
      return false;
    }

    // Get user from localStorage
    const userStr = localStorage.getItem('user');
    if (userStr) {
      this.currentUser = JSON.parse(userStr);
    }

    this.setupUI();
    this.attachEventListeners();
    return true;
  }

  setupUI() {
    this.messageContainer.innerHTML = `
      <div class="flex flex-col h-full bg-white dark:bg-slate-800 rounded-xl shadow-lg transition-colors">
        <!-- Chat Header -->
        <div class="bg-gradient-to-r from-indigo-500 to-violet-600 p-4 rounded-t-xl text-white">
          <h3 class="font-bold flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            AI Financial Advisor
          </h3>
          <p class="text-xs text-white/80 mt-1">Get personalized financial guidance</p>
        </div>

        <!-- Messages Area -->
        <div id="advisor-messages" class="flex-1 overflow-y-auto p-4 space-y-4">
          <div class="flex gap-3">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10.5 1.5H3.75A2.25 2.25 0 001.5 3.75v12.5A2.25 2.25 0 003.75 18.5h12.5a2.25 2.25 0 002.25-2.25V9.5m-15-4h4m-4 3h6m-6 3h4m8.5-8.5l-3.5 3.5m0 0l3.5 3.5m-3.5-3.5l3.5-3.5m-3.5 3.5l-3.5 3.5"/>
                </svg>
              </div>
            </div>
            <div class="flex-1">
              <p class="text-sm font-semibold text-slate-900 dark:text-white">FinPass AI</p>
              <p class="text-sm text-slate-600 dark:text-slate-300 mt-1">Hello! I'm your AI financial advisor. Ask me anything about your finances, investments, goals, budgeting, or financial planning. I'll provide personalized advice based on your profile.</p>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t border-slate-200 dark:border-slate-700 p-4 transition-colors">
          <div class="flex gap-3">
            <input
              id="advisor-input"
              type="text"
              placeholder="Ask me about your finances..."
              class="flex-1 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
            />
            <button
              id="advisor-send"
              class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-lg font-semibold flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              <span>Send</span>
            </button>
          </div>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-2">💡 Tip: Ask questions like "What should I do with my savings?" or "How can I achieve my financial goals?"</p>
        </div>
      </div>
    `;

    this.inputField = document.getElementById('advisor-input');
    this.sendButton = document.getElementById('advisor-send');
  }

  attachEventListeners() {
    if (this.sendButton) {
      this.sendButton.addEventListener('click', () => this.sendMessage());
    }
    if (this.inputField) {
      this.inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }
  }

  async sendMessage() {
    const message = this.inputField?.value?.trim();
    if (!message || this.isLoading) return;

    if (!this.currentUser) {
      this.addMessage('system', 'Please log in to use the advisor.');
      return;
    }

    // Add user message to UI
    this.addMessage('user', message);
    this.inputField.value = '';
    this.setLoading(true);

    try {
      // Prepare context from user data
      const context = {
        monthly_income: this.currentUser.financials?.['monthly-income'] || 0,
        monthly_expenses: this.currentUser.financials?.['monthly-expenses'] || 0,
        total_savings: this.currentUser.financials?.['total-savings'] || 0,
        debt: this.currentUser.financials?.debt || 0,
        risk_appetite: this.currentUser['Risk-Appetite'] || 'Moderate'
      };

      // Send to API
      const response = await fetch('/api/advisor/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          email: this.currentUser.email,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        this.addMessage('advisor', data.response);
      } else {
        this.addMessage('system', `Error: ${data.error || 'Failed to get response'}`);
      }
    } catch (error) {
      console.error('❌ Advisor chat error:', error);
      this.addMessage('system', `Sorry, I encountered an error. Please try again later. (${error.message})`);
    } finally {
      this.setLoading(false);
    }
  }

  addMessage(sender, text) {
    const messagesDiv = document.getElementById('advisor-messages');
    if (!messagesDiv) return;

    const messageEl = document.createElement('div');
    messageEl.className = 'flex gap-3 animate-slide-up';

    if (sender === 'user') {
      messageEl.innerHTML = `
        <div class="flex-1"></div>
        <div class="flex-shrink-0">
          <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">
            ${this.currentUser?.Name?.[0]?.toUpperCase() || 'U'}
          </div>
        </div>
        <div class="flex-1 max-w-xs">
          <p class="text-sm bg-indigo-600 text-white rounded-lg px-4 py-2">${this.escapeHtml(text)}</p>
        </div>
      `;
    } else if (sender === 'advisor') {
      messageEl.innerHTML = `
        <div class="flex-shrink-0">
          <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.5 1.5H3.75A2.25 2.25 0 001.5 3.75v12.5A2.25 2.25 0 003.75 18.5h12.5a2.25 2.25 0 002.25-2.25V9.5"/>
            </svg>
          </div>
        </div>
        <div class="flex-1 max-w-xs">
          <p class="text-sm font-semibold text-slate-900 dark:text-white mb-1">FinPass AI</p>
          <div class="text-sm bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100 rounded-lg px-4 py-2 whitespace-pre-wrap">${this.escapeHtml(text)}</div>
        </div>
      `;
    } else if (sender === 'system') {
      messageEl.innerHTML = `
        <div class="flex-1 flex justify-center">
          <p class="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-700 px-3 py-1 rounded-full">${this.escapeHtml(text)}</p>
        </div>
      `;
    }

    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  setLoading(isLoading) {
    this.isLoading = isLoading;
    if (this.sendButton) {
      this.sendButton.disabled = isLoading;
      this.sendButton.innerHTML = isLoading
        ? '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Sending...</span>'
        : '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg><span>Send</span>';
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize when dashboard loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const advisor = new AdvisorChatbot();
    advisor.init();
  });
} else {
  const advisor = new AdvisorChatbot();
  advisor.init();
}
