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

  const action = (agent.message || "UNKNOWN").toUpperCase();
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