import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initializing...");

let charts = {};
let currentUser = null;

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
  const savings = Math.max(0, income - expenses);

  document.getElementById('metric-income').textContent = formatCurrency(income);
  document.getElementById('metric-expense').textContent = formatCurrency(expenses);
  document.getElementById('metric-savings').textContent = formatCurrency(savings);
  document.getElementById('metric-debt').textContent = formatCurrency(debt);

  console.log("💰 Metrics populated");
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  const name = user.Name || 'User';
  const age = user.Age || '-';
  const employment = user['employment-status'] || 'Not Specified';

  document.getElementById('user-name').textContent = name;
  document.getElementById('user-email').textContent = user.email || 'user@example.com';

  const profileName = document.getElementById('profile-name');
  const profileAge = document.getElementById('profile-age');
  const profileStatus = document.getElementById('profile-status');

  if (profileName) profileName.textContent = name;
  if (profileAge) profileAge.textContent = age;
  if (profileStatus) profileStatus.textContent = employment;

  const riskAppetite = safeExtract(user, 'investments.risk-opt', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.invest-amt', 0);
  const goalDuration = safeExtract(user, 'Goal.target-time', 0);

  const investmentRisk = document.getElementById('investment-risk');
  const investmentAmt = document.getElementById('investment-amt');
  const investmentTimeline = document.getElementById('investment-timeline');

  if (investmentRisk) investmentRisk.textContent = riskAppetite;
  if (investmentAmt) investmentAmt.textContent = formatCurrency(investmentAmount);
  if (investmentTimeline) investmentTimeline.textContent = goalDuration ? `${goalDuration} months` : '-';

  console.log("👤 Profile populated");
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};

    if (goalData.error) {
      console.warn('⚠️ Goal data error:', goalData.error);
      return;
    }

    const targetAmount = safeExtract(goalData, 'target_amount', 0);
    const expectedCorpus = safeExtract(goalData, 'expected_corpus', 0);
    const probability = safeExtract(goalData, 'goal_probability', 0);

    const goalTarget = document.getElementById('goal-target');
    const goalCorpus = document.getElementById('goal-corpus');
    const goalProb = document.getElementById('goal-prob');

    if (goalTarget) goalTarget.textContent = formatCurrency(targetAmount);
    if (goalCorpus) goalCorpus.textContent = formatCurrency(expectedCorpus);
    if (goalProb) goalProb.textContent = `${probability}%`;

    const statusBadge = document.getElementById('goal-status');
    if (statusBadge) {
      if (probability >= 70) {
        statusBadge.textContent = '✅ On Track';
        statusBadge.style.background = '#10b981';
      } else if (probability >= 50) {
        statusBadge.textContent = '⚠️ At Risk';
        statusBadge.style.background = '#f59e0b';
      } else {
        statusBadge.textContent = '❌ Off Track';
        statusBadge.style.background = '#ef4444';
      }
    }

    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

// ===== CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) return;

  if (charts.incomeExpense) charts.incomeExpense.destroy();

  charts.incomeExpense = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Monthly'],
      datasets: [
        { label: 'Income', data: [income], backgroundColor: '#10b981', borderRadius: 8 },
        { label: 'Expenses', data: [expenses], backgroundColor: '#ef4444', borderRadius: 8 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: true, position: 'top' } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: v => '₹' + v.toLocaleString('en-IN') }
        }
      }
    }
  });
  console.log("✅ Income vs Expenses chart created");
}

function createHealthScoreChart(analytics) {
  const ctx = document.getElementById('healthScoreChart');
  if (!ctx) return;

  if (charts.healthScore) charts.healthScore.destroy();

  const score = analytics?.financial_health === "Excellent" ? 85 :
                analytics?.financial_health === "Good" ? 65 :
                analytics?.financial_health === "Needs Improvement" ? 45 : 60;

  const status = document.getElementById('health-status');
  if (status) {
    if (score >= 75) {
      status.textContent = '✅ Excellent';
      status.style.color = '#10b981';
    } else if (score >= 50) {
      status.textContent = '⚠️ Good';
      status.style.color = '#f59e0b';
    } else {
      status.textContent = '❌ Needs Work';
      status.style.color = '#ef4444';
    }
  }

  charts.healthScore = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Health Score', 'Remaining'],
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [
          score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444',
          '#e5e7eb'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } }
    }
  });
  console.log("✅ Health Score chart created");
}

function createExpenseBreakdownChart() {
  const ctx = document.getElementById('expenseBreakdownChart');
  if (!ctx) return;

  if (charts.expenseBreakdown) charts.expenseBreakdown.destroy();

  charts.expenseBreakdown = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Fixed (60%)', 'Variable (30%)', 'Discretionary (10%)'],
      datasets: [{
        data: [60, 30, 10],
        backgroundColor: ['#4f46e5', '#7c3aed', '#f59e0b'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
  console.log("✅ Expense Breakdown chart created");
}

function createSavingsRatioChart(analytics) {
  const ctx = document.getElementById('savingsRatioChart');
  if (!ctx) return;

  if (charts.savingsRatio) charts.savingsRatio.destroy();

  const ratio = (analytics?.savings_ratio || 0.2) * 100;

  charts.savingsRatio = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Savings Ratio %',
        data: [18, 19, 20, 21, 19, ratio],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: true, position: 'top' } },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: v => v + '%' }
        }
      }
    }
  });
  console.log("✅ Savings Ratio chart created");
}

// ===== LOAD ANALYTICS =====
async function loadAnalytics(user) {
  try {
    const response = await apiFetch(`/api/analytics/${user.email}`);
    const analytics = response.analytics || {};

    createExpenseBreakdownChart();
    createSavingsRatioChart(analytics);
    createHealthScoreChart(analytics);
    console.log("📈 Analytics loaded");
  } catch (err) {
    console.warn('⚠️ Analytics unavailable:', err.message);
  }
}

// ===== LOAD GOALS SECTION =====
async function loadGoalsSection(user) {
  try {
    // ── Goal Intelligence ──────────────────────────────────────────────────────
    const goalRes = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const gd = goalRes.goal_intelligence || {};

    const goalName     = user?.Goal?.goal || '—';
    const targetAmt    = gd.target_amount  || safeExtract(user, 'Goal.target-amt', 0);
    const timeline     = gd.goal_horizon_months || safeExtract(user, 'Goal.target-time', 0);
    const risk         = user?.Goal?.risk || safeExtract(user, 'investments.risk-opt', 'moderate');
    const corpus       = gd.expected_corpus || 0;
    const probability  = gd.goal_probability || 0;
    const sip          = safeExtract(user, 'investments.invest-amt', 0);

    document.getElementById('g-name').textContent     = goalName;
    document.getElementById('g-target').textContent   = formatCurrency(targetAmt);
    document.getElementById('g-timeline').textContent = timeline ? `${timeline} months` : '—';
    document.getElementById('g-risk').textContent     = risk;
    document.getElementById('g-corpus').textContent   = formatCurrency(corpus);
    document.getElementById('g-sip').textContent      = formatCurrency(sip);
    document.getElementById('g-prob-ring').textContent = `${probability}%`;

    // ── Progress Ring Chart ────────────────────────────────────────────────────
    const ringCtx = document.getElementById('goalProgressChart');
    if (ringCtx) {
      if (charts.goalProgress) charts.goalProgress.destroy();
      const color = probability >= 70 ? '#10b981' : probability >= 50 ? '#f59e0b' : '#ef4444';
      charts.goalProgress = new Chart(ringCtx, {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [probability, 100 - probability],
            backgroundColor: [color, 'rgba(255,255,255,0.05)'],
            borderWidth: 0,
            borderRadius: 6
          }]
        },
        options: {
          cutout: '78%',
          responsive: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
      });
    }

    // ── Allocation Donut Chart ─────────────────────────────────────────────────
    const allocCtx = document.getElementById('goalAllocationChart');
    if (allocCtx) {
      if (charts.goalAlloc) charts.goalAlloc.destroy();
      const equity = risk === 'high' ? 60 : risk === 'medium' ? 50 : 30;
      const debt   = risk === 'high' ? 25 : risk === 'medium' ? 35 : 50;
      const cash   = 100 - equity - debt;
      charts.goalAlloc = new Chart(allocCtx, {
        type: 'doughnut',
        data: {
          labels: [`Equity (${equity}%)`, `Debt (${debt}%)`, `Cash (${cash}%)`],
          datasets: [{
            data: [equity, debt, cash],
            backgroundColor: ['#6366f1', '#8b5cf6', '#f59e0b'],
            borderWidth: 0,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 12 } } } }
        }
      });
    }

    // ── AI Investment Insight ──────────────────────────────────────────────────
    const loadingEl = document.getElementById('insight-loading');
    const contentEl = document.getElementById('insight-content');
    const errorEl   = document.getElementById('insight-error');
    const textEl    = document.getElementById('insight-text');

    try {
      const insightRes = await apiFetch(`/api/ai/investment-insight/${user.email}`);
      const insightText = insightRes.insight || 'No insight available.';

      if (loadingEl) loadingEl.classList.add('hidden');
      if (contentEl) contentEl.classList.remove('hidden');
      if (textEl) textEl.textContent = insightText;
      console.log('🤖 AI insight loaded');
    } catch (aiErr) {
      console.warn('⚠️ AI insight failed:', aiErr.message);
      if (loadingEl) loadingEl.classList.add('hidden');
      if (errorEl) errorEl.classList.remove('hidden');
    }

    console.log('🎯 Goals section loaded');
  } catch (err) {
    console.warn('⚠️ Goals section failed:', err.message);
  }
}

// ===== LOAD INSIGHTS =====
async function loadInsights(user) {
  try {
    const container = document.getElementById('insights-container');
    if (!container) return;

    const income = safeExtract(user, 'financials.monthly-income', 0);
    const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
    const debt = safeExtract(user, 'financials.debt', 0);

    const insights = [];

    if (expenses > income * 0.8) {
      insights.push({
        category: 'Spending',
        impact_area: 'Monthly Budget',
        message: 'Your expenses are high. Consider cutting discretionary spending.',
        severity: 'high',
        confidence_score: 0.9
      });
    }

    if (debt > income * 3) {
      insights.push({
        category: 'Debt',
        impact_area: 'Liability',
        message: 'Your debt-to-income ratio is concerning. Prioritize debt reduction.',
        severity: 'high',
        confidence_score: 0.85
      });
    }

    if (income - expenses > income * 0.2) {
      insights.push({
        category: 'Saving',
        impact_area: 'Wealth Growth',
        message: 'Great savings rate! Consider diversifying investments.',
        severity: 'low',
        confidence_score: 0.95
      });
    }

    if (insights.length === 0) {
      insights.push({
        category: 'General',
        impact_area: 'Overview',
        message: 'Your financial situation is stable. Monitor spending and continue investing.',
        severity: 'low',
        confidence_score: 0.8
      });
    }

    renderInsights(insights);
    console.log("💡 Insights generated");
  } catch (err) {
    console.warn('⚠️ Insights unavailable:', err.message);
  }
}

function renderInsights(insights) {
  const container = document.getElementById('insights-container');
  if (!container) return;

  const severityMap = {
    high:   { badge: 'bg-red-500/15 text-red-400',    icon: '🔴', border: 'border-red-500/15' },
    medium: { badge: 'bg-amber-500/15 text-amber-400', icon: '🟡', border: 'border-amber-500/15' },
    low:    { badge: 'bg-emerald-500/15 text-emerald-400', icon: '🟢', border: 'border-emerald-500/15' },
  };

  container.innerHTML = '';
  insights.forEach(insight => {
    const s = severityMap[insight.severity] || severityMap.low;
    const card = document.createElement('div');
    card.className = `insight-card border ${s.border} rounded-2xl p-5 space-y-3`;
    card.style.background = 'rgba(255,255,255,0.03)';

    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="text-base">${s.icon}</span>
          <span class="text-sm font-semibold text-slate-200">${insight.category}</span>
        </div>
        <span class="insight-badge text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${s.badge}">${insight.impact_area}</span>
      </div>
      <p class="text-slate-400 text-sm leading-relaxed">${insight.message}</p>
      <div class="flex items-center justify-between pt-1">
        <div class="flex-1 bg-white/5 rounded-full h-1.5 mr-3">
          <div class="h-1.5 rounded-full" style="width:${Math.round((insight.confidence_score||0)*100)}%; background: linear-gradient(90deg,#6366f1,#8b5cf6);"></div>
        </div>
        <span class="text-xs text-slate-500">Confidence: ${Math.round((insight.confidence_score||0)*100)}%</span>
      </div>
    `;
    container.appendChild(card);
  });
}

// ===== SECTION NAVIGATION =====
function setupSectionNavigation() {
  // Navigation is handled in dashboard.html inline script via data-section.
  // This function is kept for compatibility but page-level script does the work.
  const navItems = document.querySelectorAll('.nav-item[data-section]');
  const sections = document.querySelectorAll('.section');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const section = item.dataset.section;

      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      sections.forEach(s => s.classList.remove('active-section'));
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) targetSection.classList.add('active-section');

      if (section === 'analytics' && currentUser) loadAnalytics(currentUser);
      else if (section === 'goals' && currentUser) loadGoalsSection(currentUser);
      else if (section === 'insights' && currentUser) loadInsights(currentUser);
    });
  });
}

// ===== LOGOUT =====
window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/login.html';
  }
};

// ===== INITIALIZE =====
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const user = await loadUserData();
    if (!user) return;

    const financials = populateMetrics(user);
    populateProfile(user);
    await populateGoalData(user);

    createIncomeExpenseChart(financials.income, financials.expenses);

    try {
      const analyticsResponse = await apiFetch(`/api/analytics/${user.email}`);
      createHealthScoreChart(analyticsResponse.analytics || {});
    } catch (err) {
      console.warn('⚠️ Initial analytics failed:', err.message);
    }

    await loadInsights(user);
    setupSectionNavigation();

    document.getElementById('btn-refresh')?.addEventListener('click', () => {
      window.location.reload();
    });

    document.getElementById('btn-agent')?.addEventListener('click', () => {
      window.location.href = './advisor.html';
    });

    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});