

import { apiFetch } from "../api.js";
import { formatCurrency, safeExtract } from "../utils/formatting.js";


export function populateProfileData() {
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


export function setupProfileEditor() {
  const editBtn = document.getElementById('profile-edit-btn');
  const editForm = document.getElementById('profile-edit-form');
  const readOnlyView = document.getElementById('profile-read-only');
  const cancelBtn = document.getElementById('profile-cancel-btn');

  editBtn.addEventListener('click', () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) return;

    const name = user.Name || '';
    const email = user.email || '';
    const age = user.Age || '';
    const emp = user['employment-status'] || '';
    const inc = safeExtract(user, 'financials.monthly-income', '');
    const exp = safeExtract(user, 'financials.monthly-expenses', '');
    const risk = safeExtract(user, 'investments.risk-opt', '');

    const nameEl = document.getElementById('edit-name');
    const emailEl = document.getElementById('edit-email');
    const ageEl = document.getElementById('edit-age');
    const empEl = document.getElementById('edit-employment');
    const incEl = document.getElementById('edit-income');
    const expEl = document.getElementById('edit-expenses');
    const riskEl = document.getElementById('edit-risk');

    if (nameEl) { nameEl.value = name; nameEl.placeholder = name || 'Enter Full Name'; }
    if (emailEl) { emailEl.value = email; emailEl.placeholder = email || 'user@example.com'; }
    if (ageEl) { ageEl.value = age; ageEl.placeholder = age ? `Current DB: ${age}` : 'Age (years)'; }
    if (empEl) { empEl.value = emp; }
    if (incEl) { incEl.value = inc; incEl.placeholder = inc ? `Current DB: ₹${inc}` : 'Monthly Income'; }
    if (expEl) { expEl.value = exp; expEl.placeholder = exp ? `Current DB: ₹${exp}` : 'Monthly Expenses'; }
    if (riskEl) { riskEl.value = risk; }

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
