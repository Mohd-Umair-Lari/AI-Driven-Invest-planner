import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initializing...");

let charts = {};
let currentUser = null;
let metricsData = {};

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value || 0);
}

function safeExtract(obj, path, defaultVal = 0) {
  if (!obj || typeof obj !== 'object') return defaultVal;
  const keys = path.split('.');
  let value = obj;
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      return defaultVal;
    }
  }
  return value ?? defaultVal;
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

function populateMetrics(user) {
  const income = safeExtract(user, 'financials.monthly-income', 0);
  const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
  const debt = safeExtract(user, 'financials.debt', 0);
  const portfolio = safeExtract(user, 'investments.invest-amt', 500000);

  document.getElementById('metric-income').textContent = formatCurrency(income);
  document.getElementById('metric-debt').textContent = formatCurrency(debt);
  document.getElementById('metric-portfolio').textContent = formatCurrency(portfolio);

  const name = user.Name || 'User';
  document.getElementById('sidebar-name').textContent = name;
  document.getElementById('sidebar-email').textContent = user.email || 'user@example.com';
  document.getElementById('hdr-name').textContent = name;
  document.getElementById('sidebar-avatar').textContent = name.charAt(0).toUpperCase();

  const surplus = Math.max(0, income - expenses - debt);

  metricsData = { income, expenses, debt, surplus, portfolio };

  createCashFlowChart(debt, surplus, expenses);

  console.log("💰 Metrics populated");
  return metricsData;
}

async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};

    const targetAmount = safeExtract(goalData, 'target_amount', 2100000);
    const expectedCorpus = safeExtract(goalData, 'expected_corpus', 500000);
    const timeline = safeExtract(user, 'Goal.target-time', 24);
    const goalName = safeExtract(user, 'Goal.goal', 'Luxury Car');

    let probability = safeExtract(goalData, 'goal_probability', 24);
    if (probability > 100) probability = 100;

    document.getElementById('metric-goal-target').textContent = formatCurrency(targetAmount);
    document.getElementById('metric-goal-name').textContent = goalName;

    document.getElementById('goal-progress-name').textContent = goalName;
    document.getElementById('goal-progress-pct').textContent = `${Math.round(probability)}% COMPLETE`;
    document.getElementById('goal-progress-total').textContent = formatCurrency(targetAmount);

    const bar = document.getElementById('goal-progress-bar');
    if (bar) bar.style.width = `${probability}%`;

    const timeEl = document.getElementById('goal-progress-time');
    if (timeEl) timeEl.textContent = `${timeline} months`;

    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

function createCashFlowChart(debt, surplus, expenses, targetId = 'cashFlowChart') {
  const ctx = document.getElementById(targetId);
  if (!ctx) {
    console.warn(`Canvas #${targetId} not found`);
    return;
  }

  const chartKey = targetId === 'cashFlowChartTab' ? 'cashFlowTab' : 'cashFlow';

  if (charts[chartKey]) {
    charts[chartKey].destroy();
  }

  charts[chartKey] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Debt Repayment', 'Investable Surplus', 'Living Expenses'],
      datasets: [{
        data: [debt || 12000, surplus || 50000, expenses || 45000],
        backgroundColor: ['#f59e0b', '#10b981', '#ef4444'],
        borderWidth: 5,
        borderColor: '#ffffff',
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: { 
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ' ' + context.label + ': ' + formatCurrency(context.raw);
            }
          }
        }
      }
    }
  });
  console.log("✅ Cash Flow chart created on #" + targetId);
}

window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/';
  }
};

function setupNavigation() {
  const navItems = document.querySelectorAll('#sidebar-nav .sidebar-item');
  const contentTabs = document.querySelectorAll('.content-tab');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.getAttribute('data-target');
      if (!targetId) return;

      navItems.forEach(n => {
          n.classList.remove('active', 'text-indigo-600', 'dark:text-indigo-400', 'bg-indigo-50', 'dark:bg-indigo-900/20');
          n.classList.add('text-slate-600', 'dark:text-slate-300');
      });

      item.classList.add('active', 'bg-indigo-50', 'dark:bg-indigo-900/20');
      item.classList.remove('text-slate-600', 'dark:text-slate-300');

      contentTabs.forEach(tab => {
        if (tab.id === `content-${targetId}`) {
          tab.classList.remove('hidden');
          if (targetId === 'profile') {
            populateProfileData();
          }
          if (targetId === 'cashflow') {

            console.log("📊 Cash flow tab opened");
          }
        } else {
          tab.classList.add('hidden');
        }
      });
    });
  });
}

function populateProfileData() {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) return;

  document.getElementById('profile-name-display').textContent = user.Name || '-';
  document.getElementById('profile-email-display').textContent = user.email || '-';
  document.getElementById('profile-age-display').textContent = user.Age || '-';
  document.getElementById('profile-employment-display').textContent = user['employment-status'] || '-';

  const income = safeExtract(user, 'financials.monthly-income', 0);
  const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
  const risk = safeExtract(user, 'investments.risk-opt', '-');

  document.getElementById('profile-income-display').textContent = formatCurrency(income);
  document.getElementById('profile-expenses-display').textContent = formatCurrency(expenses);
  document.getElementById('profile-risk-display').textContent = risk;

  console.log("👤 Profile data loaded");
}

function setupProfileEditor() {
  const editBtn = document.getElementById('profile-edit-btn');
  const editForm = document.getElementById('profile-edit-form');
  const readOnlyView = document.getElementById('profile-read-only');
  const cancelBtn = document.getElementById('profile-cancel-btn');

  editBtn.addEventListener('click', () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) return;

    document.getElementById('edit-name').value = user.Name || '';
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-age').value = user.Age || '';
    document.getElementById('edit-employment').value = user['employment-status'] || '';
    document.getElementById('edit-income').value = safeExtract(user, 'financials.monthly-income', '') || '';
    document.getElementById('edit-expenses').value = safeExtract(user, 'financials.monthly-expenses', '') || '';
    document.getElementById('edit-risk').value = safeExtract(user, 'investments.risk-opt', '') || '';

    readOnlyView.style.display = 'none';
    editForm.style.display = 'block';
  });

  cancelBtn.addEventListener('click', () => {

    editForm.style.display = 'none';
    readOnlyView.style.display = 'flex';
  });

  editForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) return;

    const updatedData = {
      Name: document.getElementById('edit-name').value,
      Age: document.getElementById('edit-age').value,
      'employment-status': document.getElementById('edit-employment').value,
      financials: {
        'monthly-income': Number(document.getElementById('edit-income').value) || 0,
        'monthly-expenses': Number(document.getElementById('edit-expenses').value) || 0,
        debt: safeExtract(user, 'financials.debt', 0),
        'em-fund-opted': safeExtract(user, 'financials.em-fund-opted', false),
      },
      investments: {
        'risk-opt': document.getElementById('edit-risk').value,
        'prefered-mode': safeExtract(user, 'investments.prefered-mode', ''),
        'invest-amt': safeExtract(user, 'investments.invest-amt', 0),
      },
      Goal: user.Goal || {},
      progress: user.progress || {},
    };

    try {
      const response = await apiFetch(`/api/user/${user.email}`, {
        method: 'PUT',
        body: JSON.stringify(updatedData)
      });

      if (response.status === 'success') {

        const updatedUser = {
          ...user,
          ...updatedData,
          _id: user._id,
          email: user.email,
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));

        const successMsg = document.getElementById('profile-success');
        successMsg.classList.add('show');
        setTimeout(() => {
          successMsg.classList.remove('show');
        }, 3000);

        editForm.style.display = 'none';
        readOnlyView.style.display = 'flex';
        populateProfileData();

        document.getElementById('sidebar-name').textContent = updatedData.Name;
        document.getElementById('hdr-name').textContent = updatedData.Name;

        console.log("✅ Profile updated successfully");
      } else {
        throw new Error('Update failed');
      }
    } catch (err) {
      console.error("❌ Profile update error:", err);
      const errorMsg = document.getElementById('profile-error');
      errorMsg.classList.add('show');
      setTimeout(() => {
        errorMsg.classList.remove('show');
      }, 3000);
    }
  });
}

const _COLOR_MAP = {
  red:    { border: "border-red-200 dark:border-red-700",    tag: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",    icon: "#ef4444" },
  orange: { border: "border-orange-200 dark:border-orange-700", tag: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300", icon: "#f97316" },
  amber:  { border: "border-amber-200 dark:border-amber-700",  tag: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",  icon: "#f59e0b" },
  green:  { border: "border-emerald-200 dark:border-emerald-700", tag: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300", icon: "#10b981" },
  indigo: { border: "border-indigo-200 dark:border-indigo-700", tag: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300", icon: "#6366f1" },
  slate:  { border: "border-slate-200 dark:border-slate-600",  tag: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",  icon: "#64748b" },
};

async function loadRecommendedActions(user) {
  const loading = document.getElementById('rec-loading');
  const list    = document.getElementById('rec-actions-list');
  const badge   = document.getElementById('rec-health-badge');
  if (!list) return;

  try {
    const data = await apiFetch(`/api/recommended-actions/${user.email}`);
    const actions = data.actions || [];

    if (badge && data.financial_health) {
      const healthColors = {
        "Excellent":        "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
        "Good":             "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
        "Needs Improvement":"bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
        "Critical":         "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
      };
      badge.textContent = `Financial Health: ${data.financial_health}`;
      badge.className = `text-xs font-semibold px-3 py-1 rounded-full ${healthColors[data.financial_health] || "bg-slate-100 text-slate-600"}`;
      badge.classList.remove('hidden');
    }

    list.innerHTML = actions.map(action => {
      const c = _COLOR_MAP[action.color] || _COLOR_MAP.slate;
      return `
        <div class="border ${c.border} rounded-xl p-4 hover:shadow-md cursor-default transition-all bg-white dark:bg-slate-800 flex items-start gap-3">
          <div class="mt-0.5 shrink-0 w-2 h-2 rounded-full mt-2" style="background:${c.icon}"></div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200">${action.title}</h4>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${c.tag}">${action.tag}</span>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">${action.subtitle}</p>
          </div>
        </div>`;
    }).join('');

    if (loading) loading.classList.add('hidden');
    list.classList.remove('hidden');

  } catch (err) {
    console.warn('⚠️ Recommended actions failed:', err.message);
    if (loading) loading.classList.add('hidden');
    list.innerHTML = `<p class="text-sm text-slate-400">Could not load recommendations. Please try refreshing.</p>`;
    list.classList.remove('hidden');
  }
}

function setupChatbot() {
  const chatInput    = document.getElementById('ai-chat-input');
  const chatSend     = document.getElementById('ai-chat-send');
  const chatMessages = document.getElementById('ai-chat-messages');

  if (!chatInput || !chatSend || !chatMessages) return;

  const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);

  function appendUserMsg(text) {
    const div = document.createElement('div');
    div.className = 'chat-user-msg';
    div.innerHTML = `<p class="chat-user-text">${escapeHtml(text)}</p>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendAiMsg(text) {
    const div = document.createElement('div');
    div.className = 'ai-chat-card';

    const formatted = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul class="chat-list">$1</ul>')
      .replace(/\n/g, '<br>');
    div.innerHTML = `
      <div class="flex justify-between items-center mb-2">
        <span class="chat-response-tag">FinPass AI</span>
      </div>
      <p class="chat-ai-text">${formatted}</p>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendError(msg) {
    const div = document.createElement('div');
    div.className = 'ai-chat-card';
    div.innerHTML = `<p class="chat-ai-text" style="color:#ef4444;">⚠️ ${escapeHtml(msg)}</p>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'chat-typing';
    div.id = 'chat-typing-indicator';
    div.innerHTML = `
      <span></span><span></span><span></span>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  const handleSend = async () => {
    const text = chatInput.value.trim();
    if (!text) return;

    const user = currentUser || JSON.parse(localStorage.getItem('user') || '{}');
    if (!user?.email) {
      appendError('Please log in to use the AI advisor.');
      return;
    }

    chatInput.value = '';
    chatInput.disabled = true;
    chatSend.disabled  = true;

    appendUserMsg(text);
    const typingEl = showTyping();

    try {
      const res = await apiFetch('/api/advisor/chat', {
        method: 'POST',
        body: JSON.stringify({
          email:      user.email,
          question:   text,
          session_id: sessionId,
          context: {
            monthly_income:   user.financials?.['monthly-income']   || 0,
            monthly_expenses: user.financials?.['monthly-expenses'] || 0,
            debt:             user.financials?.debt                 || 0,
            risk_appetite:    user.investments?.['risk-opt']        || 'moderate',
          }
        })
      });

      typingEl.remove();
      appendAiMsg(res.response || 'Sorry, I did not get a response. Please try again.');

    } catch (err) {
      typingEl.remove();
      if (err.message?.includes('401')) {
        appendError('Session expired. Please log in again.');
      } else if (err.message?.includes('timeout') || err.name === 'AbortError') {
        appendError('The request timed out. The AI server may be waking up — please try again in a moment.');
      } else {
        appendError('Something went wrong: ' + (err.message || 'Unknown error'));
      }
    } finally {
      chatInput.disabled = false;
      chatSend.disabled  = false;
      chatInput.focus();
    }
  };

  chatSend.addEventListener('click', handleSend);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    setupNavigation();
    setupProfileEditor();
    setupChatbot();

    const user = await loadUserData();
    if (!user) return;

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

window.toggleSidebar = function() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;
  
  if (window.innerWidth >= 768) {
    // Desktop mode
    sidebar.classList.toggle('desktop-collapsed');
  } else {
    // Mobile mode
    if (!overlay) return;
    if (sidebar.classList.contains('-translate-x-full')) {
      // Open sidebar
      sidebar.classList.remove('-translate-x-full');
      overlay.classList.remove('hidden');
      setTimeout(() => { overlay.classList.remove('opacity-0'); }, 10);
    } else {
      // Close sidebar
      sidebar.classList.add('-translate-x-full');
      overlay.classList.add('opacity-0');
      setTimeout(() => { overlay.classList.add('hidden'); }, 300);
    }
  }
};