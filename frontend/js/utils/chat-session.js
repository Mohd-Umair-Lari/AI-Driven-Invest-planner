/**
 * Shared chat session utilities.
 * Used by both the dashboard chatbot and the standalone advisor page.
 */

export const CHAT_SESSION_STORAGE = 'finpass_active_chat_session';

/**
 * Generate a unique chat session ID.
 * @returns {string}
 */
export function newChatSessionId() {
  return 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9);
}

/**
 * Build a localStorage key for persisting the active session per user.
 * @param {string} email
 * @returns {string}
 */
export function chatStorageKey(email) {
  return `${CHAT_SESSION_STORAGE}_${email}`;
}
