import { apiFetch } from "./api.js";

let step = 0;
const steps = document.querySelectorAll(".step");
const dots = document.querySelectorAll(".dot");
const params = new URLSearchParams(window.location.search);

function buildRegistrationPayload() {
  return {
    email: JSON.parse(localStorage.getItem("user"))?.email,

    Goal: {
      goal: document.getElementById("goal-name")?.value,
      "target-amt": Number(document.getElementById("goal-amount")?.value),
      "target-time": Number(document.getElementById("goal-time")?.value)
    },

    financials: {
      "monthly-income": Number(document.getElementById("income")?.value),
      "monthly-expenses": Number(document.getElementById("expenses")?.value),
      debt: Number(document.getElementById("debt")?.value),
      "em-fund-opted": document.getElementById("emergency")?.checked
    },

    investments: {
      "risk-opt": document.getElementById("risk")?.value,
      "prefered-mode": document.getElementById("mode")?.value,
      "invest-amt": Number(document.getElementById("invest-amt")?.value)
    }
  };
}

function hydrateWizard(data) {
  Object.entries(data).forEach(([section, values]) => {
    if (typeof values !== "object") return;

    Object.entries(values).forEach(([key, val]) => {
      const el = document.getElementById(`${section}-${key}`);
      if (el) {
        if (el.type === "checkbox") el.checked = val;
        else el.value = val;
      }
    });
  });
}

async function loadResumeState() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user?.email) return;

  try {
    const res = await apiFetch(`/api/onboarding/status/${user.email}`);
    const onboarding = res.onboarding;

    if (onboarding &&(onboarding.state === "in_progress" || onboarding.state === "cancelled")) {
      step = Number(onboarding.current_step) || 0;
      if (onboarding.data) {
        hydrateWizard(onboarding.data);
      }
    }
  } catch (err) {
    console.error("Failed to resume onboarding", err);
  }
}

function show() {
  steps.forEach((s, i) => s.classList.toggle("active", i === step));
  dots.forEach((d, i) => d.classList.toggle("active", i <= step));
}


window.nextStep = async () => {
  const payload = buildRegistrationPayload(); 
  if (!payload.email) {
    alert("User not logged in");
    return;
  }
  const nextStep = step + 1;

  await apiFetch("/api/onboarding/save", {
    method: "POST",
    body: JSON.stringify({
      email: payload.email,
      step: nextStep,
      payload
    })
  });

  step = nextStep;
  show();
};

window.prevStep = () => {
  if (step > 0) {
    step -= 1;
    show();
  }
};

window.cancelOnboarding = async () => {
  const confirmCancel = confirm(
    "Are you sure you want to pause onboarding? You can resume later."
  );

  if (!confirmCancel) return;

  const user = JSON.parse(localStorage.getItem("user"));
  if (!user?.email) return;

  try {
    await apiFetch("/api/onboarding/cancel", {
      method: "POST",
      body: JSON.stringify({
        email: user.email,
        current_step: step
      })
    });

    window.location.href = "/dashboard.html";
  } catch (err) {
    console.error("Failed to cancel onboarding", err);
    alert("Failed to pause onboarding");
  }
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

    await apiFetch("/api/onboarding/complete", {
      method: "POST",
      body: JSON.stringify({ email: user.email })
    });

    const updated = await apiFetch(`/api/user/${user.email}`);
    localStorage.setItem("user", JSON.stringify(updated.user));
    localStorage.setItem("onboardingCompleted", "true");

    window.location.href = "/dashboard.html";

  } catch (err) {
    console.error(err);
    alert("Failed to complete onboarding");
  }
};
(async () => {
  await loadResumeState();
  show();
})();