import { apiFetch } from "./api.js";

let step = 0;
const steps = document.querySelectorAll(".step");
const dots = document.querySelectorAll(".dot");
const params = new URLSearchParams(window.location.search);
const isResume = params.get("resume") === "true";

async function loadResumeState() {
  if (!isResume) return;

  const user = JSON.parse(localStorage.getItem("user"));
  if (!user?.email) return;

  try {
    const res = await apiFetch(`/api/onboarding/status/${user.email}`);

    if (res.current_step !== null && typeof res.current_step === "number") {
      step = res.current_step;
      show();
    }
  } catch (err) {
    console.error("Failed to resume onboarding", err);
  }
}

function show() {
  steps.forEach((s, i) => s.classList.toggle("active", i === step));
  dots.forEach((d, i) => d.classList.toggle("active", i <= step));
}

show();
loadResumeState();

function persistStep() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user?.email) return;

  apiFetch(`/api/onboarding/start`, {
    method: "POST",
    body: JSON.stringify({ email: user.email })
  }).catch(() => {});
}

window.next = () => {
  if (step < steps.length - 1) {
    step++;
    show();
    persistStep();
  }
};

window.prev = () => {
  if (step > 0) {
    step--;
    show();
    persistStep();
  }
};

window.cancelOnboarding = async () => {
  const confirmCancel = confirm(
    "Are you sure you want to cancel onboarding? You can complete it later."
  );

  if (!confirmCancel) return;

  const user = JSON.parse(localStorage.getItem("user"));

  localStorage.setItem("onboardingCompleted", "false");

  if (user?.email) {
    apiFetch(`/api/user/${user.email}/onboarding/cancel`, {
      method: "POST"
    }).catch(() => {});
  }

  step = 0;
  show();

  window.location.href = "/dashboard.html";
};


window.submitWizard = async () => {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) return alert("Not logged in");

  const payload = {
    Goal: {
      goal: document.getElementById("goal-name").value,
      "target-amt": Number(document.getElementById("goal-amount").value),
      "target-time": Number(document.getElementById("goal-time").value)
    },

    financials: {
      "monthly-income": Number(document.getElementById("income").value),
      "monthly-expenses": Number(document.getElementById("expenses").value),
      debt: Number(document.getElementById("debt").value),
      "em-fund-opted": document.getElementById("emergency").checked
    },

    investments: {
      "risk-opt": document.getElementById("risk").value,
      "prefered-mode": document.getElementById("mode").value,
      "invest-amt": Number(document.getElementById("invest-amt").value)
    },

    progress: {
      tenure: 1,
      start_date: new Date().toISOString().split("T")[0],
      "auto-adjust": false
    }
  };

  try {
    await apiFetch(`/api/user/${user.email}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });

    // reload fresh user
    const updated = await apiFetch(`/api/user/${user.email}`);
    localStorage.setItem("user", JSON.stringify(updated.user));
    localStorage.setItem("onboardingCompleted", "true");

    window.location.href = "/dashboard.html";

  } catch (err) {
    alert("Failed to save onboarding");
    console.error(err);
  }
};
