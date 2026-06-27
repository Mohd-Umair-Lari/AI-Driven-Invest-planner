/**
 * Dashboard navigation component.
 * Handles sidebar tab switching and mobile sidebar toggle.
 */

/**
 * Set up sidebar navigation: tab switching and profile tab trigger.
 * @param {Function} onProfileTab - callback when profile tab is opened
 */
export function setupNavigation(onProfileTab) {
  const navItems = document.querySelectorAll('#sidebar-nav .sidebar-item');
  const contentTabs = document.querySelectorAll('.content-tab');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.getAttribute('data-target');
      if (!targetId) return;

      navItems.forEach(n => {
        n.classList.remove('active', 'text-indigo-600', 'dark:text-indigo-400', 'bg-indigo-50', 'dark:bg-indigo-900/20');
        n.classList.add('text-slate-600', 'dark:text-slate-300');
      });

      item.classList.add('active', 'bg-indigo-50', 'dark:bg-indigo-900/20');
      item.classList.remove('text-slate-600', 'dark:text-slate-300');

      contentTabs.forEach(tab => {
        if (tab.id === `content-${targetId}`) {
          tab.classList.remove('hidden');
          if (targetId === 'profile' && typeof onProfileTab === 'function') {
            onProfileTab();
          }
          if (targetId === 'cashflow') {
            console.log("📊 Cash flow tab opened");
          }
        } else {
          tab.classList.add('hidden');
        }
      });
    });
  });
}

/**
 * Toggle sidebar visibility on mobile.
 */
export function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar || !overlay) return;

  if (sidebar.classList.contains('-translate-x-full')) {
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
    setTimeout(() => { overlay.classList.remove('opacity-0'); }, 10);
  } else {
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('opacity-0');
    setTimeout(() => { overlay.classList.add('hidden'); }, 300);
  }
}
