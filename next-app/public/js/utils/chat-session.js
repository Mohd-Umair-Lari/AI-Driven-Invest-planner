

export const CHAT_SESSION_STORAGE = 'finpass_active_chat_session';


export function newChatSessionId() {
  return 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9);
}


export function chatStorageKey(email) {
  return `${CHAT_SESSION_STORAGE}_${email}`;
}
