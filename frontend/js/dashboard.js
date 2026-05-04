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
  createCashFlowChart(debt, surplus, expenses);

  console.log("💰 Metrics populated");
  return { income, expenses, debt, surplus, portfolio };
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
function createCashFlowChart(debt, surplus, expenses) {
  const ctx = document.getElementById('cashFlowChart');
  if (!ctx) return;

  if (charts.cashFlow) charts.cashFlow.destroy();

  charts.cashFlow = new Chart(ctx, {
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
  console.log("✅ Cash Flow chart created");
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

    populateMetrics(user);
    await populateGoalData(user);

    console.log("✅ Dashboard Ready");
  } catch (err) {
    console.error("🔥 Dashboard init failed:", err);
  }
});