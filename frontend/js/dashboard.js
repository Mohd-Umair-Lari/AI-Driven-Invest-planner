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
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  document.getElementById('user-name').textContent = user.Name || 'User';
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  document.getElementById('profile-name').textContent = user.Name || '-';
  document.getElementById('profile-age').textContent = user.Age || '-';
  document.getElementById('profile-status').textContent = user['employment-status'] || '-';
  
  const riskAppetite = safeExtract(user, 'Goal.risk', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.amount', 0);
  const goalDuration = safeExtract(user, 'Goal.duration_months', 0);
  
  document.getElementById('investment-risk').textContent = riskAppetite;
  document.getElementById('investment-amt').textContent = formatCurrency(investmentAmount);
  document.getElementById('investment-timeline').textContent = goalDuration ? `${goalDuration} months` : '-';
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    const targetAmount = safeExtract(goalData, 'target_amount', 0);
    const expectedCorpus = safeExtract(goalData, 'expected_corpus', 0);
    const probability = safeExtract(goalData, 'goal_probability', 0);
    
    document.getElementById('goal-target').textContent = formatCurrency(targetAmount);
    document.getElementById('goal-corpus').textContent = formatCurrency(expectedCorpus);
    document.getElementById('goal-prob').textContent = `${probability}%`;
    
    const statusBadge = document.getElementById('goal-status');
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
    
    const progressFill = document.getElementById('goal-progress');
    progressFill.style.width = `${Math.min(100, probability)}%`;
    
    document.getElementById('detail-probability').textContent = `${probability}%`;
    document.getElementById('detail-verdict').textContent = goalData.verdict || 'Analyzing...';
    document.getElementById('detail-roi').textContent = `${goalData.roi_assumed || 0}%`;
    
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
}

function createHealthScoreChart(analytics) {
  const ctx = document.getElementById('healthScoreChart');
  if (!ctx) return;
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const score = analytics?.financial_health || 65;
  const status = document.getElementById('health-status');
  
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
    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } }
  });
}

function createExpenseBreakdownChart() {
  const ctx = document.getElementById('expenseBreakdownChart');
  if (!ctx) return;
  
  if (charts.expenseBreakdown) charts.expenseBreakdown.destroy();
  
  charts.expenseBreakdown = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Fixed', 'Variable', 'Emergency'],
      datasets: [{
        data: [40, 40, 20],
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
    
    if (response.status === 'error') {
      openModal(`<h2>⚠️ Analysis Error</h2><p>${response.message}</p>`);
      return;
    }
    
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
    transition: all 0.2s ease;
  }
  .modal-close:hover {
    background: #e0d5ff;
  }
`;
document.head.appendChild(style);
import { apiFetch } from "./api.js";

console.log("📊 Dashboard loaded");

let charts = {};
let currentUser = null;

// ===== DATA FORMATTING =====
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

// ===== LOAD USER DATA =====
async function loadUserData() {
  let user = JSON.parse(localStorage.getItem("user"));
  
  if (!user) {
    window.location.href = "/index.html";
    return null;
  }
  
  currentUser = user;
  return user;
}

// ===== POPULATE METRICS =====
function populateMetrics(user) {
  const income = safeExtract(user, 'financials.monthly-income', 0);
  const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
  const debt = safeExtract(user, 'financials.debt', 0);
  const savings = income - expenses;
  
  document.getElementById('metric-income').textContent = formatCurrency(income);
  document.getElementById('metric-expense').textContent = formatCurrency(expenses);
  document.getElementById('metric-savings').textContent = formatCurrency(Math.max(0, savings));
  document.getElementById('metric-debt').textContent = formatCurrency(debt);
  
  return { income, expenses, debt, savings };
}

// ===== POPULATE PROFILE =====
function populateProfile(user) {
  document.getElementById('user-name').textContent = user.Name || 'User';
  document.getElementById('user-email').textContent = user.email || 'user@example.com';
  
  document.getElementById('profile-name').textContent = user.Name || '-';
  document.getElementById('profile-age').textContent = user.Age || '-';
  document.getElementById('profile-status').textContent = user['employment-status'] || '-';
  
  const riskAppetite = safeExtract(user, 'Goal.risk', 'Moderate');
  const investmentAmount = safeExtract(user, 'investments.amount', 0);
  const goalDuration = safeExtract(user, 'Goal.duration_months', 0);
  
  document.getElementById('investment-risk').textContent = riskAppetite;
  document.getElementById('investment-amt').textContent = formatCurrency(investmentAmount);
  document.getElementById('investment-timeline').textContent = `${goalDuration} months` || '-';
}

// ===== POPULATE GOAL DATA =====
async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};
    
    const targetAmount = safeExtract(goalData, 'target_amount', 0);
    const expectedCorpus = safeExtract(goalData, 'expected_corpus', 0);
    const probability = safeExtract(goalData, 'goal_probability', 0);
    
    document.getElementById('goal-target').textContent = formatCurrency(targetAmount);
    document.getElementById('goal-corpus').textContent = formatCurrency(expectedCorpus);
    document.getElementById('goal-prob').textContent = `${probability}%`;
    
    // Set goal status
    const statusBadge = document.getElementById('goal-status');
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
    
    // Set progress
    const progressFill = document.getElementById('goal-progress');
    progressFill.style.width = `${Math.min(100, probability)}%`;
    
    // Store for goal section
    document.getElementById('detail-probability').textContent = `${probability}%`;
    document.getElementById('detail-verdict').textContent = goalData.verdict || '-';
    document.getElementById('detail-roi').textContent = `${goalData.roi_assumed || 0}%`;
    
  } catch (err) {
    console.error('Failed to load goal data:', err);
  }
}

// ===== CREATE CHARTS =====
function createIncomeExpenseChart(income, expenses) {
  const ctx = document.getElementById('incomeExpenseChart');
  if (!ctx) return;
  
  if (charts.incomeExpense) charts.incomeExpense.destroy();
  
  charts.incomeExpense = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Monthly'],
      datasets: [
        {
          label: 'Income',
          data: [income],
          backgroundColor: '#10b981',
          borderRadius: 8,
          borderSkipped: false
        },
        {
          label: 'Expenses',
          data: [expenses],
          backgroundColor: '#ef4444',
          borderRadius: 8,
          borderSkipped: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '₹' + value.toLocaleString('en-IN');
            }
          }
        }
      }
    }
  });
}

function createHealthScoreChart(analytics) {
  const ctx = document.getElementById('healthScoreChart');
  if (!ctx) return;
  
  if (charts.healthScore) charts.healthScore.destroy();
  
  const healthScore = analytics?.financial_health || 65;
  const healthStatus = document.getElementById('health-status');
  
  if (healthScore >= 75) {
    healthStatus.textContent = 'Excellent';
    healthStatus.style.color = '#10b981';
  } else if (healthScore >= 50) {
    healthStatus.textContent = 'Good';
    healthStatus.style.color = '#f59e0b';
  } else {
    healthStatus.textContent = 'Needs Work';
    healthStatus.style.color = '#ef4444';
  }
  
  charts.healthScore = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Health Score', 'Remaining'],
      datasets: [{
        data: [healthScore, 100 - healthScore],
        backgroundColor: [
          healthScore >= 75 ? '#10b981' : healthScore >= 50 ? '#f59e0b' : '#ef4444',
          '#e5e7eb'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function createExpenseBreakdownChart(expenses) {
  const ctx = document.getElementById('expenseBreakdownChart');
  if (!ctx) return;
  
  if (charts.expenseBreakdown) charts.expenseBreakdown.destroy();
  
  charts.expenseBreakdown = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Fixed', 'Variable', 'Emergency'],
      datasets: [{
        data: [40, 40, 20],
        backgroundColor: ['#4f46e5', '#7c3aed', '#f59e0b'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

function createSavingsRatioChart(analytics) {
  const ctx = document.getElementById('savingsRatioChart');
  if (!ctx) return;
  
  if (charts.savingsRatio) charts.savingsRatio.destroy();
  
  const savingsRatio = (analytics?.savings_ratio || 0.2) * 100;
  
  charts.savingsRatio = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Savings Ratio %',
        data: [18, 19, 20, 21, 19, savingsRatio],
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
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}

// ===== LOAD ANALYTICS =====
async function loadAnalytics(user) {
  try {
    const response = await apiFetch(`/api/analytics/${user.email}`);
    const analytics = response.analytics || {};
    
    createExpenseBreakdownChart(user.financials);
    createSavingsRatioChart(analytics);
    createHealthScoreChart(analytics);
    
  } catch (err) {
    console.error('Failed to load analytics:', err);
  }
}

// ===== LOAD AI INSIGHTS =====
async function loadInsights(user) {
  try {
    const container = document.getElementById('insights-container');
    if (!container) return;
    
    // Generate synthetic insights based on user data
    const income = safeExtract(user, 'financials.monthly-income', 0);
    const expenses = safeExtract(user, 'financials.monthly-expenses', 0);
    const debt = safeExtract(user, 'financials.debt', 0);
    
    const insights = [];
    
    if (expenses > income * 0.8) {
      insights.push({
        category: 'spending',
        impact_area: 'Monthly Budget',
        message: 'Your expenses are high relative to income. Consider cutting discretionary spending.',
        severity: 'high',
        confidence_score: 0.9
      });
    }
    
    if (debt > income * 3) {
      insights.push({
        category: 'debt',
        impact_area: 'Liability',
        message: 'Your debt-to-income ratio is concerning. Prioritize debt reduction.',
        severity: 'high',
        confidence_score: 0.85
      });
    }
    
    if (income - expenses > income * 0.2) {
      insights.push({
        category: 'saving',
        impact_area: 'Wealth Growth',
        message: 'Great savings rate! Consider diversifying investments.',
        severity: 'low',
        confidence_score: 0.95
      });
    }
    
    if (insights.length === 0) {
      insights.push({
        category: 'general',
        impact_area: 'Overview',
        message: 'Your financial situation is stable. Monitor spending and continue investing.',
        severity: 'low',
        confidence_score: 0.8
      });
    }
    
    renderInsights(insights);
  } catch (err) {
    console.error('Failed to load insights:', err);
  }
}

function renderInsights(insights) {
  const container = document.getElementById('insights-container');
  if (!container) return;
  
  container.innerHTML = '';
  
  insights.forEach(insight => {
    const card = document.createElement('div');
    card.className = `insight-card ${insight.severity}`;
    
    const categoryLabel = insight.category.charAt(0).toUpperCase() + insight.category.slice(1);
    
    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${categoryLabel}</span>
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

// ===== LOAD AI ADVISOR =====
async function loadAIAdvisor(user) {
  try {
    const response = await apiFetch(`/api/analyze-finances/${user.email}`);
    
    if (response.status === 'error') {
      alert('Unable to get AI analysis. Please ensure your financial data is complete.');
      return;
    }
    
    const analysis = response;
    
    let actionEmoji = '📊';
    if (analysis.financial_health_score > 80) actionEmoji = '✅';
    else if (analysis.financial_health_score < 50) actionEmoji = '⚠️';
    
    const message = `
      <h2>🤖 AI Financial Analysis</h2>
      <div style="background: #f3e8ff; padding: 16px; border-radius: 10px; margin: 16px 0;">
        <p><strong>Health Score:</strong> ${analysis.financial_health_score}/100</p>
        <p><strong>Analysis:</strong> ${analysis.analysis}</p>
      </div>
      <div style="margin: 16px 0;">
        <p style="font-weight: 600; margin-bottom: 8px;">📋 Recommendations:</p>
        <ul style="margin-left: 20px; line-height: 1.8;">
          ${(analysis.recommendations || []).map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div style="background: #dbeafe; padding: 12px; border-radius: 10px; margin-top: 16px;">
        <p style="font-weight: 600; margin-bottom: 8px;">📈 Suggested Allocation:</p>
        <p>Equity: ${analysis.investment_strategy?.equity || 0}% | Debt: ${analysis.investment_strategy?.debt || 0}% | Cash: ${analysis.investment_strategy?.cash || 0}%</p>
      </div>
    `;
    
    openModal(message);
  } catch (err) {
    console.error('Failed to load AI advisor:', err);
    openModal(`<h2>⚠️ Analysis Unavailable</h2><p>${err.message || 'Please complete your financial profile first.'}</p>`);
  }
}

// ===== MODAL FUNCTIONS =====
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
      
      // Update active nav
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      
      // Update visible sections
      sections.forEach(s => s.style.display = 'none');
      
      const targetSection = document.getElementById(`${section}-section`);
      if (targetSection) {
        targetSection.style.display = 'block';
      }
      
      // Load section-specific data
      if (section === 'analytics' && currentUser) {
        loadAnalytics(currentUser);
      } else if (section === 'insights' && currentUser) {
        loadInsights(currentUser);
      }
    });
  });
}

// ===== INITIALIZE DASHBOARD =====
document.addEventListener('DOMContentLoaded', async () => {
  const user = await loadUserData();
  if (!user) return;
  
  // Populate all data
  const financials = populateMetrics(user);
  populateProfile(user);
  await populateGoalData(user);
  
  // Create charts
  createIncomeExpenseChart(financials.income, financials.expenses);
  
  // Load analytics for health score
  try {
    const analyticsResponse = await apiFetch(`/api/analytics/${user.email}`);
    createHealthScoreChart(analyticsResponse.analytics || {});
  } catch (err) {
    console.error('Failed to load health score:', err);
  }
  
  // Load insights
  await loadInsights(user);
  
  // Setup navigation
  setupSectionNavigation();
  
  // Setup action buttons
  document.getElementById('btn-refresh')?.addEventListener('click', async () => {
    window.location.reload();
  });
  
  document.getElementById('btn-agent')?.addEventListener('click', async () => {
    await loadAIAdvisor(user);
  });
});

// ===== LOGOUT =====
window.logout = () => {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.removeItem('user');
    window.location.href = '/index.html';
  }
};

// Add modal styles dynamically
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
    transition: all 0.2s ease;
  }
  
  .modal-close:hover {
    background: #e0d5ff;
  }
`;
document.head.appendChild(style);

console.log('✅ Dashboard fully loaded');
import { apiFetch } from "./api.js";
import { fetchInsights } from "./api.js";
console.log("🔥 dashboard.js loaded");

async function loadInsights() {
  const user = JSON.parse(localStorage.getItem("user"));

  if (!user) return;

  const financialState = {
    income: parseFloat(user.financials?.income || 0),
    expenses: parseFloat(user.financials?.expenses || 0),
    savings: parseFloat(user.financials?.savings || 0),
    debt: parseFloat(user.financials?.debt || 0),
    risk_score: parseFloat(user.investments?.risk_score || 0.5),
    investment_exposure: parseFloat(user.investments?.exposure || 0.5),
    goal_horizon_months: parseInt(user.Goal?.duration_months || 60),
    emergency_fund_months: parseFloat(user.financials?.emergency_fund_months || 3)
  };

  const response = await fetchInsights(financialState);
  renderInsights(response.insights || []);
}

function renderInsights(insights) {
  const container = document.getElementById("insights-container");
  container.innerHTML = "";

  if (!insights.length) {
    container.innerHTML = `<div class="insight-empty">No active signals</div>`;
    return;
  }

  insights.forEach(insight => {
    const card = document.createElement("div");
    card.className = `insight-card ${insight.severity}`;

    card.innerHTML = `
      <div class="insight-top">
        <span class="insight-category">${insight.category.toUpperCase()}</span>
        <span class="insight-impact">${insight.impact_area}</span>
      </div>
      <div class="insight-message">${insight.message}</div>
      <div class="insight-confidence">
        Confidence: ${(insight.confidence_score * 100).toFixed(0)}%
      </div>
    `;

    container.appendChild(card);
  });
}

function openModal(html) {
  const backdrop = document.getElementById("modal-backdrop");
  const content = document.getElementById("modal-content");
  content.innerHTML = html;
  backdrop.classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modal-backdrop")?.classList.add("hidden");
}

function mergeBufferedData(user, buffer) {
  if (!buffer) return user;

  return {
    ...user,
    Goal: buffer.Goal ?? user.Goal,
    financials: buffer.financials ?? user.financials,
    investments: buffer.investments ?? user.investments,
    progress: buffer.progress ?? user.progress
  };
}

async function hydrateUserWithBufferedOnboarding(user) {
  try {
    const res = await apiFetch(`/api/onboarding/status/${user.email}`);
    const onboarding = res.onboarding;

    if (
      onboarding &&
      (onboarding.state === "cancelled" || onboarding.state === "in_progress") &&
      onboarding.data
    ) {
      const merged = mergeBufferedData(user, onboarding.data);
      localStorage.setItem("user", JSON.stringify(merged));
      return merged;
    }

    return user;
  } catch (err) {
    console.error("❌ Failed to hydrate onboarding buffer", err);
    return user;
  }
}

async function checkOnboardingStatus(user) {
  if (!user?.email) return;

  try {
    const res = await apiFetch(`/api/onboarding/status/${user.email}`);
    const onboarding = res.onboarding;

    if (
      onboarding &&
      (onboarding.state === "cancelled" || onboarding.state === "in_progress")
    ) {
      const container = document.getElementById("resume-onboarding-container");
      const btn = document.getElementById("resume-onboarding-btn");

      if (!container || !btn) return;

      container.style.display = "block";
      btn.onclick = () => {
        window.location.href = "/wizard.html";
      };
    }
  } catch (err) {
    console.error("Failed to check onboarding status", err);
  }
}

async function loadAnalytics(email) {
  const { analytics } = await apiFetch(`/api/analytics/${email}`);

  openModal(`
    <h2>Financial Analytics</h2>
    <p><b>Financial Health:</b> ${analytics.financial_health}</p>
    <p><b>Savings Ratio:</b> ${(analytics.savings_ratio * 100).toFixed(1)}%</p>
    <p><b>Expense Ratio:</b> ${(analytics.expense_ratio * 100).toFixed(1)}%</p>
    <p><b>Risk Score:</b> ${analytics.risk_score}</p>
  `);
}

async function loadGoalIntelligence(email) {
  const { goal_intelligence: g } = await apiFetch(`/api/goal-intelligence/${email}`);

  openModal(`
    <h2>Goal Intelligence</h2>
    <p><b>Goal Probability:</b> ${g.goal_probability}%</p>
    <p><b>Expected Corpus:</b> ₹${g.expected_corpus}</p>
    <p><b>Target Amount:</b> ₹${g.target_amount}</p>
    <p><b>Gap:</b> ₹${Math.abs(g.gap)}</p>
    <hr/>
    <p><b>Risk Level:</b> ${g.risk_level}</p>
    <p><b>Assumed ROI:</b> ${g.roi_assumed}%</p>
    <div class="decision-badge ${g.goal_probability >= 70 ? "good" : "bad"}">
      ${g.verdict}
    </div>
  `);
}

async function loadAgentDecision(email) {
  const data = await apiFetch(`/api/agent/${email}`);

  if (!data?.agent) {
    openModal(`<h2>AI Decision Advisor</h2><p>Decision unavailable.</p>`);
    return;
  }

  const agent = data.agent || {};

  const action = (agent.action || "UNKNOWN").toUpperCase();
  const message = agent.message || "Decision unavailable.";
  const reason = agent.reason || null;

  openModal(`
    <h2>AI Decision Advisor</h2>
    <span class="agent-badge ${action.toLowerCase()}">${action}</span>
    <p class="agent-message">${message}</p>
    ${reason ? `<hr/><p><b>Reason:</b> ${reason}</p>` : ""}
  `);
}

function renderDashboard(user) {
  setText("profile-name", user.Name);
  setText("profile-email", user.email);
  setText("profile-age", user.Age);
  setText("profile-status", user["employement-status"]);

  setText("goal-name", user.Goal?.goal);
  setText("goal-amount", extract(user.Goal?.["target-amt"]));
  setText("goal-time", extract(user.Goal?.["target-time"]));

  setText("income", extract(user.financials?.["monthly-income"]));
  setText("expenses", extract(user.financials?.["monthly-expenses"]));
  setText("debt", extract(user.financials?.debt));
  setText("emergency", user.financials?.["em-fund-opted"] ? "Yes" : "No");

  setText("risk", user.investments?.["risk-opt"]);
  setText("mode", user.investments?.["prefered-mode"]);
  setText("invest-amt", extract(user.investments?.["invest-amt"]));

  setText("tenure", extract(user.progress?.tenure));
  setText("start-date", user.progress?.start_date);
  setText("auto-adjust", user.progress?.["auto-adjust"] ? "Enabled" : "Disabled");
}

document.addEventListener("DOMContentLoaded", async () => {
  let user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    window.location.href = "/";
    return;
  }

  document.getElementById("modal-close")?.addEventListener("click", closeModal);
  document.getElementById("modal-backdrop")?.addEventListener("click", e => {
    if (e.target.id === "modal-backdrop") closeModal();
  });

  document.getElementById("btn-analytics")
    ?.addEventListener("click", () => loadAnalytics(user.email));

  document.getElementById("btn-goal")
    ?.addEventListener("click", () => loadGoalIntelligence(user.email));

  document.getElementById("btn-agent")
    ?.addEventListener("click", () => loadAgentDecision(user.email));

  user = await hydrateUserWithBufferedOnboarding(user);
  renderDashboard(user);
  checkOnboardingStatus(user);
});

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? "-";
}

function extract(v) {
  if (v == null) return "-";
  if (typeof v === "object") return Object.values(v)[0];
  return v;
}

window.logout = () => {
  localStorage.removeItem("user");
  window.location.href = "/";
};

document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeModal();
});

document.addEventListener("DOMContentLoaded", () => {
  loadInsights();
});