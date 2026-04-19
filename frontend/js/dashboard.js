import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initialized");

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
    window.location.href = "/index.html";
    return null;
  }
  
  // If user doesn't have financial data, initialize test data
  if (!user.financials || Object.keys(user.financials).length === 0) {
    try {
      console.log("📝 Initializing test data for user...");
      const response = await apiFetch(`/api/init-test-data/${user.email}`, {
        method: "POST"
      });
      user = response.user;
      localStorage.setItem("user", JSON.stringify(user));
      console.log("✅ Test data initialized");
    } catch (err) {
      console.warn("⚠️ Could not initialize test data:", err.message);
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
  
  console.log("💰 Metrics populated:", { income, expenses, savings, debt });
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  const name = user.Name || 'User';
  const age = user.Age || '-';
  const employment = user['employment-status'] || 'Not Specified';
  
  document.getElementById('user-name').textContent = name;
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  // Personal Information
  const profileName = document.getElementById('profile-name');
  const profileAge = document.getElementById('profile-age');
  const profileStatus = document.getElementById('profile-status');
  
  if (profileName) profileName.textContent = name;
  if (profileAge) profileAge.textContent = age;
  if (profileStatus) profileStatus.textContent = employment;
  
  // Investment Details
  const riskAppetite = safeExtract(user, 'investments.risk-opt', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.invest-amt', 0);
  const goalDuration = safeExtract(user, 'Goal.target-time', 0);
  
  const investmentRisk = document.getElementById('investment-risk');
  const investmentAmt = document.getElementById('investment-amt');
  const investmentTimeline = document.getElementById('investment-timeline');
  
  if (investmentRisk) investmentRisk.textContent = riskAppetite;
  if (investmentAmt) investmentAmt.textContent = formatCurrency(investmentAmount);
  if (investmentTimeline) investmentTimeline.textContent = goalDuration ? `${goalDuration} months` : '-';
  
  console.log("👤 Profile populated:", { name, age, employment });
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    if (goalData.error) {
      console.warn('⚠️ Goal data has error:', goalData.error);
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
    
    // Goal Status Badge
    const statusBadge = document.getElementById('goal-status');
    if (statusBadge) {
      if (probability >= 70) {
        statusBadge.textContent = '✓ On Track';
        statusBadge.style.background = '#10b981';
      } else if (probability >= 50) {
        statusBadge.textContent = '◐ At Risk';
        statusBadge.style.background = '#f59e0b';
      } else {
        statusBadge.textContent = '✗ Off Track';
        statusBadge.style.background = '#ef4444';
      }
    }
    
    // Progress Bar
    const progressFill = document.getElementById('goal-progress');
    if (progressFill) {
      progressFill.style.width = `${Math.min(100, probability)}%`;
    }
    
    // Details
    const detailProbability = document.getElementById('detail-probability');
    const detailVerdict = document.getElementById('detail-verdict');
    const detailRoi = document.getElementById('detail-roi');
    
    if (detailProbability) detailProbability.textContent = `${probability}%`;
    if (detailVerdict) detailVerdict.textContent = goalData.verdict || 'Analyzing...';
    if (detailRoi) detailRoi.textContent = `${goalData.roi_assumed || 8}%`;
    
    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

// ===== CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: incomeExpenseChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: healthScoreChart');
    return;
  }
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const score = analytics?.financial_health === "Excellent" ? 85 :
                analytics?.financial_health === "Good" ? 65 :
                analytics?.financial_health === "Needs Improvement" ? 45 : 60;
  
  const status = document.getElementById('health-status');
  
  if (status) {
    if (score >= 75) {
      status.textContent = 'Excellent';
      status.style.color = '#10b981';
    } else if (score >= 50) {
      status.textContent = 'Good';
      status.style.color = '#f59e0b';
    } else {
      status.textContent = 'Needs Work';
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: expenseBreakdownChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: savingsRatioChart');
    return;
  }
  
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
  
  container.innerHTML = '';
  insights.forEach(insight => {
    const card = document.createElement('div');
    card.className = `insight-card ${insight.severity}`;
    
    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${insight.category}</span>
        <span class="insight-impact">${insight.impact_area}</span>
      </div>
      <div class="insight-message">${insight.message}</div>
      <div class="insight-confidence">
        Confidence: ${Math.round((insight.confidence_score || 0) * 100)}%
      </div>
    `;
    
    container.appendChild(card);
  });
}

// ===== AI ADVISOR =====
async function loadAIAdvisor(user) {
  try {
    const response = await apiFetch(`/api/analyze-finances/${user.email}`);
    
    const analysis = response;
    const message = `
      <h2>🤖 AI Financial Analysis</h2>
      <div style="background: #f3e8ff; padding: 16px; border-radius: 10px; margin: 16px 0;">
        <p><strong>Health Score:</strong> ${analysis.financial_health_score || 'N/A'}/100</p>
        <p><strong>Analysis:</strong> ${analysis.analysis || 'Analyzing your finances...'}</p>
      </div>
      <div style="margin: 16px 0;">
        <p style="font-weight: 600; margin-bottom: 8px;">📋 Recommendations:</p>
        <ul style="margin-left: 20px; line-height: 1.8;">
          ${(analysis.recommendations || ['Monitor your spending regularly', 'Diversify your investments']).map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div style="background: #dbeafe; padding: 12px; border-radius: 10px; margin-top: 16px;">
        <p style="font-weight: 600; margin-bottom: 8px;">📈 Suggested Allocation:</p>
        <p>Equity: ${analysis.investment_strategy?.equity || '60'}% | Debt: ${analysis.investment_strategy?.debt || '30'}% | Cash: ${analysis.investment_strategy?.cash || '10'}%</p>
      </div>
    `;
    
    openModal(message);
    console.log("🤖 AI Advisor response loaded");
  } catch (err) {
    console.warn('⚠️ AI Advisor unavailable:', err.message);
    openModal(`<h2>📊 Financial Summary</h2><p>AI analysis temporarily unavailable. Your dashboard data is fully functional.</p><p><small>Status: ${err.message}</small></p>`);
  }
}

// ===== MODAL =====
function openModal(html) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.innerHTML = `
    <div class="modal-card">
      <button class="modal-close" onclick="this.closest('.modal-backdrop').remove();">&times;</button>
      <div>${html}</div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ===== SECTION NAVIGATION =====
function setupSectionNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.section');
  
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      const section = item.dataset.section;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      
      sections.forEach(s => s.style.display = 'none');
      
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) targetSection.style.display = 'block';
      
      if (section === 'analytics' && currentUser) loadAnalytics(currentUser);
      else if (section === 'insights' && currentUser) loadInsights(currentUser);
    });
  });
}

// ===== LOGOUT =====
function logout() {
  if (confirm('Logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/index.html';
  }
}

// Expose logout to window
window.logout = logout;

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
      loadAIAdvisor(user);
    });
    
    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});

// Modal styles
const style = document.createElement('style');
style.textContent = `
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-card {
    position: relative;
    background: white;
    width: 90%;
    max-width: 600px;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    max-height: 80vh;
    overflow-y: auto;
  }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border: none;
    background: #f3e8ff;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .modal-close:hover {
    background: #e9d5ff;
  }
  
  .insight-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-left: 4px solid #4f46e5;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
  }
  .insight-card.high {
    border-left-color: #ef4444;
    background: #fef2f2;
  }
  .insight-card.medium {
    border-left-color: #f59e0b;
    background: #fffbf0;
  }
  .insight-card.low {
    border-left-color: #10b981;
    background: #f0fdf4;
  }
  .insight-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
  }
  .insight-category {
    font-weight: 600;
    color: #1f2937;
  }
  .insight-impact {
    color: #6b7280;
  }
  .insight-message {
    color: #374151;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .insight-confidence {
    font-size: 12px;
    color: #6b7280;
  }
`;
document.head.appendChild(style);
import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initialized");

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
    window.location.href = "/index.html";
    return null;
  }
  
  // If user doesn't have financial data, initialize test data
  if (!user.financials || Object.keys(user.financials).length === 0) {
    try {
      console.log("📝 Initializing test data for user...");
      const response = await apiFetch(`/api/init-test-data/${user.email}`, {
        method: "POST"
      });
      user = response.user;
      localStorage.setItem("user", JSON.stringify(user));
      console.log("✅ Test data initialized");
    } catch (err) {
      console.warn("⚠️ Could not initialize test data:", err.message);
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
  
  console.log("💰 Metrics populated:", { income, expenses, savings, debt });
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  const name = user.Name || 'User';
  const age = user.Age || '-';
  const employment = user['employment-status'] || 'Not Specified';
  
  document.getElementById('user-name').textContent = name;
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  // Personal Information
  const profileName = document.getElementById('profile-name');
  const profileAge = document.getElementById('profile-age');
  const profileStatus = document.getElementById('profile-status');
  
  if (profileName) profileName.textContent = name;
  if (profileAge) profileAge.textContent = age;
  if (profileStatus) profileStatus.textContent = employment;
  
  // Investment Details
  const riskAppetite = safeExtract(user, 'investments.risk-opt', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.invest-amt', 0);
  const goalDuration = safeExtract(user, 'Goal.target-time', 0);
  
  const investmentRisk = document.getElementById('investment-risk');
  const investmentAmt = document.getElementById('investment-amt');
  const investmentTimeline = document.getElementById('investment-timeline');
  
  if (investmentRisk) investmentRisk.textContent = riskAppetite;
  if (investmentAmt) investmentAmt.textContent = formatCurrency(investmentAmount);
  if (investmentTimeline) investmentTimeline.textContent = goalDuration ? `${goalDuration} months` : '-';
  
  console.log("👤 Profile populated:", { name, age, employment });
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    if (goalData.error) {
      console.warn('⚠️ Goal data has error:', goalData.error);
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
    
    // Goal Status Badge
    const statusBadge = document.getElementById('goal-status');
    if (statusBadge) {
      if (probability >= 70) {
        statusBadge.textContent = '✓ On Track';
        statusBadge.style.background = '#10b981';
      } else if (probability >= 50) {
        statusBadge.textContent = '◐ At Risk';
        statusBadge.style.background = '#f59e0b';
      } else {
        statusBadge.textContent = '✗ Off Track';
        statusBadge.style.background = '#ef4444';
      }
    }
    
    // Progress Bar
    const progressFill = document.getElementById('goal-progress');
    if (progressFill) {
      progressFill.style.width = `${Math.min(100, probability)}%`;
    }
    
    // Details
    const detailProbability = document.getElementById('detail-probability');
    const detailVerdict = document.getElementById('detail-verdict');
    const detailRoi = document.getElementById('detail-roi');
    
    if (detailProbability) detailProbability.textContent = `${probability}%`;
    if (detailVerdict) detailVerdict.textContent = goalData.verdict || 'Analyzing...';
    if (detailRoi) detailRoi.textContent = `${goalData.roi_assumed || 8}%`;
    
    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

// ===== CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: incomeExpenseChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: healthScoreChart');
    return;
  }
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const score = analytics?.financial_health === "Excellent" ? 85 :
                analytics?.financial_health === "Good" ? 65 :
                analytics?.financial_health === "Needs Improvement" ? 45 : 60;
  
  const status = document.getElementById('health-status');
  
  if (status) {
    if (score >= 75) {
      status.textContent = 'Excellent';
      status.style.color = '#10b981';
    } else if (score >= 50) {
      status.textContent = 'Good';
      status.style.color = '#f59e0b';
    } else {
      status.textContent = 'Needs Work';
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: expenseBreakdownChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: savingsRatioChart');
    return;
  }
  
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
  
  container.innerHTML = '';
  insights.forEach(insight => {
    const card = document.createElement('div');
    card.className = `insight-card ${insight.severity}`;
    
    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${insight.category}</span>
        <span class="insight-impact">${insight.impact_area}</span>
      </div>
      <div class="insight-message">${insight.message}</div>
      <div class="insight-confidence">
        Confidence: ${Math.round((insight.confidence_score || 0) * 100)}%
      </div>
    `;
    
    container.appendChild(card);
  });
}

// ===== AI ADVISOR =====
async function loadAIAdvisor(user) {
  try {
    const response = await apiFetch(`/api/analyze-finances/${user.email}`);
    
    const analysis = response;
    const message = `
      <h2>🤖 AI Financial Analysis</h2>
      <div style="background: #f3e8ff; padding: 16px; border-radius: 10px; margin: 16px 0;">
        <p><strong>Health Score:</strong> ${analysis.financial_health_score || 'N/A'}/100</p>
        <p><strong>Analysis:</strong> ${analysis.analysis || 'Analyzing your finances...'}</p>
      </div>
      <div style="margin: 16px 0;">
        <p style="font-weight: 600; margin-bottom: 8px;">📋 Recommendations:</p>
        <ul style="margin-left: 20px; line-height: 1.8;">
          ${(analysis.recommendations || ['Monitor your spending regularly', 'Diversify your investments']).map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div style="background: #dbeafe; padding: 12px; border-radius: 10px; margin-top: 16px;">
        <p style="font-weight: 600; margin-bottom: 8px;">📈 Suggested Allocation:</p>
        <p>Equity: ${analysis.investment_strategy?.equity || '60'}% | Debt: ${analysis.investment_strategy?.debt || '30'}% | Cash: ${analysis.investment_strategy?.cash || '10'}%</p>
      </div>
    `;
    
    openModal(message);
    console.log("🤖 AI Advisor response loaded");
  } catch (err) {
    console.warn('⚠️ AI Advisor unavailable:', err.message);
    openModal(`<h2>📊 Financial Summary</h2><p>AI analysis temporarily unavailable. Your dashboard data is fully functional.</p><p><small>Status: ${err.message}</small></p>`);
  }
}

// ===== MODAL =====
function openModal(html) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.innerHTML = `
    <div class="modal-card">
      <button class="modal-close" onclick="this.closest('.modal-backdrop').remove();">&times;</button>
      <div>${html}</div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ===== SECTION NAVIGATION =====
function setupSectionNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.section');
  
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      const section = item.dataset.section;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      
      sections.forEach(s => s.style.display = 'none');
      
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) targetSection.style.display = 'block';
      
      if (section === 'analytics' && currentUser) loadAnalytics(currentUser);
      else if (section === 'insights' && currentUser) loadInsights(currentUser);
    });
  });
}

// ===== LOGOUT =====
function logout() {
  if (confirm('Logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/index.html';
  }
}

// Expose logout to window
window.logout = logout;

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
      loadAIAdvisor(user);
    });
    
    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});

// Modal styles
const style = document.createElement('style');
style.textContent = `
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-card {
    position: relative;
    background: white;
    width: 90%;
    max-width: 600px;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    max-height: 80vh;
    overflow-y: auto;
  }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border: none;
    background: #f3e8ff;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .modal-close:hover {
    background: #e9d5ff;
  }
  
  .insight-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-left: 4px solid #4f46e5;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
  }
  .insight-card.high {
    border-left-color: #ef4444;
    background: #fef2f2;
  }
  .insight-card.medium {
    border-left-color: #f59e0b;
    background: #fffbf0;
  }
  .insight-card.low {
    border-left-color: #10b981;
    background: #f0fdf4;
  }
  .insight-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
  }
  .insight-category {
    font-weight: 600;
    color: #1f2937;
  }
  .insight-impact {
    color: #6b7280;
  }
  .insight-message {
    color: #374151;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .insight-confidence {
    font-size: 12px;
    color: #6b7280;
  }
`;
document.head.appendChild(style);
import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initialized");

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
    window.location.href = "/index.html";
    return null;
  }
  
  // If user doesn't have financial data, initialize test data
  if (!user.financials || Object.keys(user.financials).length === 0) {
    try {
      console.log("📝 Initializing test data for user...");
      const response = await apiFetch(`/api/init-test-data/${user.email}`, {
        method: "POST"
      });
      user = response.user;
      localStorage.setItem("user", JSON.stringify(user));
      console.log("✅ Test data initialized");
    } catch (err) {
      console.warn("⚠️ Could not initialize test data:", err.message);
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
  
  console.log("💰 Metrics populated:", { income, expenses, savings, debt });
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  const name = user.Name || 'User';
  const age = user.Age || '-';
  const employment = user['employment-status'] || 'Not Specified';
  
  document.getElementById('user-name').textContent = name;
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  // Personal Information
  const profileName = document.getElementById('profile-name');
  const profileAge = document.getElementById('profile-age');
  const profileStatus = document.getElementById('profile-status');
  
  if (profileName) profileName.textContent = name;
  if (profileAge) profileAge.textContent = age;
  if (profileStatus) profileStatus.textContent = employment;
  
  // Investment Details
  const riskAppetite = safeExtract(user, 'investments.risk-opt', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.invest-amt', 0);
  const goalDuration = safeExtract(user, 'Goal.target-time', 0);
  
  const investmentRisk = document.getElementById('investment-risk');
  const investmentAmt = document.getElementById('investment-amt');
  const investmentTimeline = document.getElementById('investment-timeline');
  
  if (investmentRisk) investmentRisk.textContent = riskAppetite;
  if (investmentAmt) investmentAmt.textContent = formatCurrency(investmentAmount);
  if (investmentTimeline) investmentTimeline.textContent = goalDuration ? `${goalDuration} months` : '-';
  
  console.log("👤 Profile populated:", { name, age, employment });
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    if (goalData.error) {
      console.warn('⚠️ Goal data has error:', goalData.error);
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
    
    // Goal Status Badge
    const statusBadge = document.getElementById('goal-status');
    if (statusBadge) {
      if (probability >= 70) {
        statusBadge.textContent = '✓ On Track';
        statusBadge.style.background = '#10b981';
      } else if (probability >= 50) {
        statusBadge.textContent = '◐ At Risk';
        statusBadge.style.background = '#f59e0b';
      } else {
        statusBadge.textContent = '✗ Off Track';
        statusBadge.style.background = '#ef4444';
      }
    }
    
    // Progress Bar
    const progressFill = document.getElementById('goal-progress');
    if (progressFill) {
      progressFill.style.width = `${Math.min(100, probability)}%`;
    }
    
    // Details
    const detailProbability = document.getElementById('detail-probability');
    const detailVerdict = document.getElementById('detail-verdict');
    const detailRoi = document.getElementById('detail-roi');
    
    if (detailProbability) detailProbability.textContent = `${probability}%`;
    if (detailVerdict) detailVerdict.textContent = goalData.verdict || 'Analyzing...';
    if (detailRoi) detailRoi.textContent = `${goalData.roi_assumed || 8}%`;
    
    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

// ===== CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: incomeExpenseChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: healthScoreChart');
    return;
  }
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const score = analytics?.financial_health === "Excellent" ? 85 :
                analytics?.financial_health === "Good" ? 65 :
                analytics?.financial_health === "Needs Improvement" ? 45 : 60;
  
  const status = document.getElementById('health-status');
  
  if (status) {
    if (score >= 75) {
      status.textContent = 'Excellent';
      status.style.color = '#10b981';
    } else if (score >= 50) {
      status.textContent = 'Good';
      status.style.color = '#f59e0b';
    } else {
      status.textContent = 'Needs Work';
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: expenseBreakdownChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: savingsRatioChart');
    return;
  }
  
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
  
  container.innerHTML = '';
  insights.forEach(insight => {
    const card = document.createElement('div');
    card.className = `insight-card ${insight.severity}`;
    
    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${insight.category}</span>
        <span class="insight-impact">${insight.impact_area}</span>
      </div>
      <div class="insight-message">${insight.message}</div>
      <div class="insight-confidence">
        Confidence: ${Math.round((insight.confidence_score || 0) * 100)}%
      </div>
    `;
    
    container.appendChild(card);
  });
}

// ===== AI ADVISOR =====
async function loadAIAdvisor(user) {
  try {
    const response = await apiFetch(`/api/analyze-finances/${user.email}`);
    
    const analysis = response;
    const message = `
      <h2>🤖 AI Financial Analysis</h2>
      <div style="background: #f3e8ff; padding: 16px; border-radius: 10px; margin: 16px 0;">
        <p><strong>Health Score:</strong> ${analysis.financial_health_score || 'N/A'}/100</p>
        <p><strong>Analysis:</strong> ${analysis.analysis || 'Analyzing your finances...'}</p>
      </div>
      <div style="margin: 16px 0;">
        <p style="font-weight: 600; margin-bottom: 8px;">📋 Recommendations:</p>
        <ul style="margin-left: 20px; line-height: 1.8;">
          ${(analysis.recommendations || ['Monitor your spending regularly', 'Diversify your investments']).map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div style="background: #dbeafe; padding: 12px; border-radius: 10px; margin-top: 16px;">
        <p style="font-weight: 600; margin-bottom: 8px;">📈 Suggested Allocation:</p>
        <p>Equity: ${analysis.investment_strategy?.equity || '60'}% | Debt: ${analysis.investment_strategy?.debt || '30'}% | Cash: ${analysis.investment_strategy?.cash || '10'}%</p>
      </div>
    `;
    
    openModal(message);
    console.log("🤖 AI Advisor response loaded");
  } catch (err) {
    console.warn('⚠️ AI Advisor unavailable:', err.message);
    openModal(`<h2>📊 Financial Summary</h2><p>AI analysis temporarily unavailable. Your dashboard data is fully functional.</p><p><small>Status: ${err.message}</small></p>`);
  }
}

// ===== MODAL =====
function openModal(html) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.innerHTML = `
    <div class="modal-card">
      <button class="modal-close" onclick="this.closest('.modal-backdrop').remove();">&times;</button>
      <div>${html}</div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ===== SECTION NAVIGATION =====
function setupSectionNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.section');
  
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      const section = item.dataset.section;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      
      sections.forEach(s => s.style.display = 'none');
      
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) targetSection.style.display = 'block';
      
      if (section === 'analytics' && currentUser) loadAnalytics(currentUser);
      else if (section === 'insights' && currentUser) loadInsights(currentUser);
    });
  });
}

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
      loadAIAdvisor(user);
    });
    
    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});

// ===== LOGOUT =====
window.logout = () => {
  if (confirm('Logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/index.html';
  }
};

// Modal styles
const style = document.createElement('style');
style.textContent = `
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-card {
    position: relative;
    background: white;
    width: 90%;
    max-width: 600px;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    max-height: 80vh;
    overflow-y: auto;
  }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border: none;
    background: #f3e8ff;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .modal-close:hover {
    background: #e9d5ff;
  }
  
  .insight-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-left: 4px solid #4f46e5;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
  }
  .insight-card.high {
    border-left-color: #ef4444;
    background: #fef2f2;
  }
  .insight-card.medium {
    border-left-color: #f59e0b;
    background: #fffbf0;
  }
  .insight-card.low {
    border-left-color: #10b981;
    background: #f0fdf4;
  }
  .insight-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
  }
  .insight-category {
    font-weight: 600;
    color: #1f2937;
  }
  .insight-impact {
    color: #6b7280;
  }
  .insight-message {
    color: #374151;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .insight-confidence {
    font-size: 12px;
    color: #6b7280;
  }
`;
document.head.appendChild(style);
import { apiFetch } from "./api.js";

console.log("📊 Dashboard Initialized");

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
    window.location.href = "/index.html";
    return null;
  }
  
  // If user doesn't have financial data, initialize test data
  if (!user.financials || Object.keys(user.financials).length === 0) {
    try {
      console.log("📝 Initializing test data for user...");
      const response = await apiFetch(`/api/init-test-data/${user.email}`, {
        method: "POST"
      });
      user = response.user;
      localStorage.setItem("user", JSON.stringify(user));
      console.log("✅ Test data initialized");
    } catch (err) {
      console.warn("⚠️ Could not initialize test data:", err.message);
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
  
  console.log("💰 Metrics populated:", { income, expenses, savings, debt });
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  const name = user.Name || 'User';
  const age = user.Age || '-';
  const employment = user['employment-status'] || 'Not Specified';
  
  document.getElementById('user-name').textContent = name;
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  // Personal Information
  const profileName = document.getElementById('profile-name');
  const profileAge = document.getElementById('profile-age');
  const profileStatus = document.getElementById('profile-status');
  
  if (profileName) profileName.textContent = name;
  if (profileAge) profileAge.textContent = age;
  if (profileStatus) profileStatus.textContent = employment;
  
  // Investment Details
  const riskAppetite = safeExtract(user, 'investments.risk-opt', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.invest-amt', 0);
  const goalDuration = safeExtract(user, 'Goal.target-time', 0);
  
  const investmentRisk = document.getElementById('investment-risk');
  const investmentAmt = document.getElementById('investment-amt');
  const investmentTimeline = document.getElementById('investment-timeline');
  
  if (investmentRisk) investmentRisk.textContent = riskAppetite;
  if (investmentAmt) investmentAmt.textContent = formatCurrency(investmentAmount);
  if (investmentTimeline) investmentTimeline.textContent = goalDuration ? `${goalDuration} months` : '-';
  
  console.log("👤 Profile populated:", { name, age, employment });
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    if (goalData.error) {
      console.warn('⚠️ Goal data has error:', goalData.error);
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
    
    // Goal Status Badge
    const statusBadge = document.getElementById('goal-status');
    if (statusBadge) {
      if (probability >= 70) {
        statusBadge.textContent = '✓ On Track';
        statusBadge.style.background = '#10b981';
      } else if (probability >= 50) {
        statusBadge.textContent = '◐ At Risk';
        statusBadge.style.background = '#f59e0b';
      } else {
        statusBadge.textContent = '✗ Off Track';
        statusBadge.style.background = '#ef4444';
      }
    }
    
    // Progress Bar
    const progressFill = document.getElementById('goal-progress');
    if (progressFill) {
      progressFill.style.width = `${Math.min(100, probability)}%`;
    }
    
    // Details
    const detailProbability = document.getElementById('detail-probability');
    const detailVerdict = document.getElementById('detail-verdict');
    const detailRoi = document.getElementById('detail-roi');
    
    if (detailProbability) detailProbability.textContent = `${probability}%`;
    if (detailVerdict) detailVerdict.textContent = goalData.verdict || 'Analyzing...';
    if (detailRoi) detailRoi.textContent = `${goalData.roi_assumed || 8}%`;
    
    console.log("🎯 Goal data loaded");
  } catch (err) {
    console.warn('⚠️ Goal data unavailable:', err.message);
  }
}

// ===== CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: incomeExpenseChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: healthScoreChart');
    return;
  }
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const score = analytics?.financial_health === "Excellent" ? 85 :
                analytics?.financial_health === "Good" ? 65 :
                analytics?.financial_health === "Needs Improvement" ? 45 : 60;
  
  const status = document.getElementById('health-status');
  
  if (status) {
    if (score >= 75) {
      status.textContent = 'Excellent';
      status.style.color = '#10b981';
    } else if (score >= 50) {
      status.textContent = 'Good';
      status.style.color = '#f59e0b';
    } else {
      status.textContent = 'Needs Work';
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: expenseBreakdownChart');
    return;
  }
  
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
  if (!ctx) {
    console.warn('⚠️ Chart canvas not found: savingsRatioChart');
    return;
  }
  
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
  
  container.innerHTML = '';
  insights.forEach(insight => {
    const card = document.createElement('div');
    card.className = `insight-card ${insight.severity}`;
    
    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${insight.category}</span>
        <span class="insight-impact">${insight.impact_area}</span>
      </div>
      <div class="insight-message">${insight.message}</div>
      <div class="insight-confidence">
        Confidence: ${Math.round((insight.confidence_score || 0) * 100)}%
      </div>
    `;
    
    container.appendChild(card);
  });
}

// ===== AI ADVISOR =====
async function loadAIAdvisor(user) {
  try {
    const response = await apiFetch(`/api/analyze-finances/${user.email}`);
    
    const analysis = response;
    const message = `
      <h2>🤖 AI Financial Analysis</h2>
      <div style="background: #f3e8ff; padding: 16px; border-radius: 10px; margin: 16px 0;">
        <p><strong>Health Score:</strong> ${analysis.financial_health_score || 'N/A'}/100</p>
        <p><strong>Analysis:</strong> ${analysis.analysis || 'Analyzing your finances...'}</p>
      </div>
      <div style="margin: 16px 0;">
        <p style="font-weight: 600; margin-bottom: 8px;">📋 Recommendations:</p>
        <ul style="margin-left: 20px; line-height: 1.8;">
          ${(analysis.recommendations || ['Monitor your spending regularly', 'Diversify your investments']).map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div style="background: #dbeafe; padding: 12px; border-radius: 10px; margin-top: 16px;">
        <p style="font-weight: 600; margin-bottom: 8px;">📈 Suggested Allocation:</p>
        <p>Equity: ${analysis.investment_strategy?.equity || '60'}% | Debt: ${analysis.investment_strategy?.debt || '30'}% | Cash: ${analysis.investment_strategy?.cash || '10'}%</p>
      </div>
    `;
    
    openModal(message);
    console.log("🤖 AI Advisor response loaded");
  } catch (err) {
    console.warn('⚠️ AI Advisor unavailable:', err.message);
    openModal(`<h2>📊 Financial Summary</h2><p>AI analysis temporarily unavailable. Your dashboard data is fully functional.</p><p><small>Status: ${err.message}</small></p>`);
  }
}

// ===== MODAL =====
function openModal(html) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.innerHTML = `
    <div class="modal-card">
      <button class="modal-close" onclick="this.closest('.modal-backdrop').remove();">&times;</button>
      <div>${html}</div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ===== SECTION NAVIGATION =====
function setupSectionNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.section');
  
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      const section = item.dataset.section;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      
      sections.forEach(s => s.style.display = 'none');
      
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) targetSection.style.display = 'block';
      
      if (section === 'analytics' && currentUser) loadAnalytics(currentUser);
      else if (section === 'insights' && currentUser) loadInsights(currentUser);
    });
  });
}

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
      loadAIAdvisor(user);
    });
    
    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});

// ===== LOGOUT =====
window.logout = () => {
  if (confirm('Logout?')) {
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingCompleted');
    window.location.href = '/index.html';
  }
};

// Modal styles
const style = document.createElement('style');
style.textContent = `
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal-card {
    position: relative;
    background: white;
    width: 90%;
    max-width: 600px;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    max-height: 80vh;
    overflow-y: auto;
  }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border: none;
    background: #f3e8ff;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .modal-close:hover {
    background: #e9d5ff;
  }
  
  .insight-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-left: 4px solid #4f46e5;
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
  }
  .insight-card.high {
    border-left-color: #ef4444;
    background: #fef2f2;
  }
  .insight-card.medium {
    border-left-color: #f59e0b;
    background: #fffbf0;
  }
  .insight-card.low {
    border-left-color: #10b981;
    background: #f0fdf4;
  }
  .insight-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
  }
  .insight-category {
    font-weight: 600;
    color: #1f2937;
  }
  .insight-impact {
    color: #6b7280;
  }
  .insight-message {
    color: #374151;
    line-height: 1.5;
    margin-bottom: 8px;
  }
  .insight-confidence {
    font-size: 12px;
    color: #6b7280;
  }
`;
document.head.appendChild(style);
