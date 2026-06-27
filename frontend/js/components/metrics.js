/**
 * Dashboard metrics component.
 * Handles stat cards, cash flow chart, goal progress, and recommended actions.
 */

import { apiFetch } from "../api.js";
import { formatCurrency, safeExtract, escapeHtml } from "../utils/formatting.js";

let charts = {};

const _COLOR_MAP = {
  red:    { border: "border-red-200 dark:border-red-700",    tag: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",    icon: "#ef4444" },
  orange: { border: "border-orange-200 dark:border-orange-700", tag: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300", icon: "#f97316" },
  amber:  { border: "border-amber-200 dark:border-amber-700",  tag: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",  icon: "#f59e0b" },
  green:  { border: "border-emerald-200 dark:border-emerald-700", tag: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300", icon: "#10b981" },
  indigo: { border: "border-indigo-200 dark:border-indigo-700", tag: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300", icon: "#6366f1" },
  slate:  { border: "border-slate-200 dark:border-slate-600",  tag: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",  icon: "#64748b" },
};

/**
 * Create or recreate a doughnut chart showing cash flow breakdown.
 */
export function createCashFlowChart(debt, surplus, expenses, targetId = 'cashFlowChart') {
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
        backgroundColor: ['#EF4444', '#FFD700', '#1e293b'],
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

/**
 * Populate stat cards and sidebar user info.
 * @returns {object} metricsData
 */
export function populateMetrics(user) {
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

  const metricsData = { income, expenses, debt, surplus, portfolio };

  createCashFlowChart(debt, surplus, expenses);

  console.log("💰 Metrics populated");
  return metricsData;
}

/**
 * Fetch and display goal intelligence data.
 */
export async function populateGoalData(user) {
  try {
    const response = await apiFetch(`/api/goal-intelligence/${user.email}`);
    const goalData = response.goal_intelligence || {};

    const targetAmount = safeExtract(goalData, 'target_amount', 2100000);
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

/**
 * Fetch and display recommended actions.
 */
export async function loadRecommendedActions(user) {
  const loading = document.getElementById('rec-loading');
  const list = document.getElementById('rec-actions-list');
  const badge = document.getElementById('rec-health-badge');
  if (!list) return;

  try {
    const data = await apiFetch(`/api/recommended-actions/${user.email}`);
    const actions = data.actions || [];

    if (badge && data.financial_health) {
      const healthColors = {
        "Excellent":         "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
        "Good":              "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
        "Needs Improvement": "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
        "Critical":          "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
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
