import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initializing...");

let charts = {};
let currentUser = null;
let metricsData = {}; // Store metrics for chart recreation

// ===== HELPERS =====
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

// ===== LOAD USER =====
async function loadUserData() {
  let user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    window.location.href = "/login.html";
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

// ===== POPULATE METRICS =====
function populateMetrics(user) {
  const income = safeExtract(user, 'financials.monthly-income', 0);
  const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
  const debt = safeExtract(user, 'financials.debt', 0);
  const portfolio = safeExtract(user, 'investments.invest-amt', 500000); // fallback to 5L if not set

  // Stat Cards
  document.getElementById('metric-income').textContent = formatCurrency(income);
  document.getElementById('metric-debt').textContent = formatCurrency(debt);
  document.getElementById('metric-portfolio').textContent = formatCurrency(portfolio);

  // Sidebar User
  const name = user.Name || 'User';
  document.getElementById('sidebar-name').textContent = name;
  document.getElementById('sidebar-email').textContent = user.email || 'user@example.com';
  document.getElementById('hdr-name').textContent = name;
  document.getElementById('sidebar-avatar').textContent = name.charAt(0).toUpperCase();

  // Draw chart
  const surplus = Math.max(0, income - expenses - debt);
  
  // Store metrics globally for later recreation
  metricsData = { income, expenses, debt, surplus, portfolio };
  
  createCashFlowChart(debt, surplus, expenses);

  console.log("💰 Metrics populated");
  return metricsData;
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};

    const targetAmount = safeExtract(goalData, 'target_amount', 2100000);
    const expectedCorpus = safeExtract(goalData, 'expected_corpus', 500000);
    const timeline = safeExtract(user, 'Goal.target-time', 24);
    const goalName = safeExtract(user, 'Goal.goal', 'Luxury Car');
    
    // Hardcoded 24% for the visual template match if probability is 0
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

// ===== CHART =====
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
        data: [debt || 12000, surplus || 50000, expenses || 45000], // fallback data for aesthetics
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

// ===== LOGOUT =====
window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/';
  }
};

// ===== NAVIGATION & TABS =====
function setupNavigation() {
  const navItems = document.querySelectorAll('#sidebar-nav .sidebar-item');
  const contentTabs = document.querySelectorAll('.content-tab');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.getAttribute('data-target');
      if (!targetId) return;

      // Update active state on nav
      navItems.forEach(n => {
          n.classList.remove('active', 'text-indigo-600', 'dark:text-indigo-400', 'bg-indigo-50', 'dark:bg-indigo-900/20');
          n.classList.add('text-slate-600', 'dark:text-slate-300');
      });
      
      item.classList.add('active', 'bg-indigo-50', 'dark:bg-indigo-900/20');
      item.classList.remove('text-slate-600', 'dark:text-slate-300');

      // Show target content tab
      contentTabs.forEach(tab => {
        if (tab.id === `content-${targetId}`) {
          tab.classList.remove('hidden');
          if (targetId === 'profile') {
            populateProfileData();
          }
          if (targetId === 'cashflow') {
            // Cash flow tab - Sankey diagram is static SVG, no chart creation needed
            console.log("📊 Cash flow tab opened");
          }
        } else {
          tab.classList.add('hidden');
        }
      });
    });
  });
}

// ===== PROFILE MANAGEMENT =====
function populateProfileData() {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) return;

  // Populate read-only view
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

    // Populate form with current data
    document.getElementById('edit-name').value = user.Name || '';
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-age').value = user.Age || '';
    document.getElementById('edit-employment').value = user['employment-status'] || '';
    document.getElementById('edit-income').value = safeExtract(user, 'financials.monthly-income', '') || '';
    document.getElementById('edit-expenses').value = safeExtract(user, 'financials.monthly-expenses', '') || '';
    document.getElementById('edit-risk').value = safeExtract(user, 'investments.risk-opt', '') || '';

    // Switch to edit mode
    readOnlyView.style.display = 'none';
    editForm.style.display = 'block';
  });

  cancelBtn.addEventListener('click', () => {
    // Switch back to read-only mode
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
        // Update localStorage
        const updatedUser = {
          ...user,
          ...updatedData,
          _id: user._id,
          email: user.email,
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));

        // Show success message
        const successMsg = document.getElementById('profile-success');
        successMsg.classList.add('show');
        setTimeout(() => {
          successMsg.classList.remove('show');
        }, 3000);

        // Switch back to read-only and refresh display
        editForm.style.display = 'none';
        readOnlyView.style.display = 'flex';
        populateProfileData();
        
        // Update header and sidebar
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

// ===== AI CHATBOT =====
function setupChatbot() {
  const chatInput = document.getElementById('ai-chat-input');
  const chatSend = document.getElementById('ai-chat-send');
  const chatMessages = document.getElementById('ai-chat-messages');

  if (!chatInput || !chatSend || !chatMessages) return;

  const handleSend = () => {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'bg-indigo-500/20 border border-indigo-500/30 rounded-xl p-3 ml-8 mb-3 text-right';
    userMsg.innerHTML = `<p class="text-xs text-white">${text}</p>`;
    chatMessages.appendChild(userMsg);
    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add typing indicator
    const typingMsg = document.createElement('div');
    typingMsg.className = 'text-xs text-slate-500 italic mb-3';
    typingMsg.textContent = 'AI Advisor is thinking...';
    chatMessages.appendChild(typingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Simulate AI response
    setTimeout(() => {
      typingMsg.remove();
      const aiMsg = document.createElement('div');
      aiMsg.className = 'bg-white/[0.04] border border-white/5 rounded-xl p-4 mb-3 mr-4';
      aiMsg.innerHTML = `
        <div class="flex justify-between items-center mb-2">
            <span class="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded tracking-wider">RESPONSE</span>
        </div>
        <p class="text-xs text-slate-300 leading-relaxed">Based on your portfolio, prioritizing debt repayment while maintaining a 10% SIP increase is the best approach to hit your goal.</p>
      `;
      chatMessages.appendChild(aiMsg);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 1200);
  };

  chatSend.addEventListener('click', handleSend);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
  });
}

// ===== INITIALIZE =====
document.addEventListener('DOMContentLoaded', async () => {
  try {
    setupNavigation();
    setupProfileEditor();
    setupChatbot();
    
    const user = await loadUserData();
    if (!user) return;

    populateMetrics(user);
    await populateGoalData(user);

    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});