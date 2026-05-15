/**
 * chat.js — Chat polling with since= incremental updates
 */
import api from './api.js';
import auth from './auth.js';
import { showError } from './toast.js';

let currentUser = null;
let teamId = null;
let lastMessageTime = null;
let pollingInterval = null;

export async function initChat() {
  currentUser = auth.getUser();
  if (!currentUser || !currentUser.team_id) {
    window.location.href = '/team-select.html';
    return;
  }
  teamId = currentUser.team_id;

  await loadInitialMessages();
  startPolling();
  setupSendForm();
  setupVisualViewport();
}

// ── Load messages ──────────────────────────────────────────────────────────────

async function loadInitialMessages() {
  try {
    const messages = await api.get(`/teams/${teamId}/messages`);
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';
    messages.forEach(msg => appendMessage(msg));
    scrollToBottom();

    if (messages.length > 0) {
      lastMessageTime = messages[messages.length - 1].created_at;
    }
  } catch (err) {
    showError(err.message);
  }
}

async function pollMessages() {
  try {
    const since = lastMessageTime || new Date(0).toISOString();
    const path = `/teams/${teamId}/messages?since=${encodeURIComponent(since)}`;
    const messages = await api.get(path);

    if (messages && messages.length > 0) {
      const container = document.getElementById('messagesContainer');
      const wasAtBottom = isScrolledToBottom(container);

      messages.forEach(msg => appendMessage(msg));
      lastMessageTime = messages[messages.length - 1].created_at;

      if (wasAtBottom) scrollToBottom();
    }
  } catch (err) {
    // Silently ignore polling errors (offline, etc.)
    console.error('Poll error:', err);
  }
}

function startPolling() {
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(pollMessages, 5000);
}

export function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

// ── Render messages ────────────────────────────────────────────────────────────

function appendMessage(msg) {
  const container = document.getElementById('messagesContainer');
  const isMine = msg.user_id === currentUser.id;

  const wrapper = document.createElement('div');
  wrapper.dataset.msgId = msg.id;
  wrapper.className = `flex ${isMine ? 'justify-end' : 'justify-start'} gap-2 mb-3`;

  const time = new Date(msg.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  const senderInitial = (msg.user_email || '?')[0].toUpperCase();

  if (isMine) {
    wrapper.innerHTML = `
      <div class="flex flex-col items-end gap-1 max-w-[70%]">
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400 dark:text-gray-500">${time}</span>
          <button class="delete-msg-btn text-gray-300 hover:text-red-500 text-xs transition-colors" data-msg-id="${msg.id}" title="삭제">✕</button>
        </div>
        <div class="bg-indigo-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed break-words">
          ${escapeHtml(msg.content)}
        </div>
      </div>
    `;
  } else {
    wrapper.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center text-sm font-bold text-gray-600 dark:text-gray-200 shrink-0 self-end">
        ${senderInitial}
      </div>
      <div class="flex flex-col gap-1 max-w-[70%]">
        <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">${escapeHtml(msg.user_email || '알 수 없음')}</span>
        <div class="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 px-4 py-2.5 rounded-2xl rounded-tl-sm text-sm text-gray-800 dark:text-gray-100 leading-relaxed break-words shadow-sm">
          ${escapeHtml(msg.content)}
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500 ml-1">${time}</span>
      </div>
    `;
  }

  // Delete button for own messages
  const deleteBtn = wrapper.querySelector('.delete-msg-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      if (!confirm('이 메시지를 삭제할까요?')) return;
      try {
        await api.delete(`/messages/${msg.id}`);
        wrapper.remove();
      } catch (err) {
        showError(err.message);
      }
    });
  }

  container.appendChild(wrapper);
}

// ── Send form ──────────────────────────────────────────────────────────────────

function setupSendForm() {
  const form = document.getElementById('sendForm');
  const input = document.getElementById('messageInput');
  const counter = document.getElementById('charCounter');
  const sendBtn = document.getElementById('sendBtn');

  // Character counter
  input.addEventListener('input', () => {
    const len = input.value.length;
    counter.textContent = `${len}/1000`;
    sendBtn.disabled = len === 0 || len > 1000;
    if (len > 1000) {
      counter.classList.add('text-red-500');
    } else {
      counter.classList.remove('text-red-500');
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = input.value.trim();
    if (!content || content.length > 1000) return;

    sendBtn.disabled = true;
    try {
      const msg = await api.post(`/teams/${teamId}/messages`, { content });
      if (msg) {
        appendMessage(msg);
        input.value = '';
        counter.textContent = '0/1000';
        lastMessageTime = msg.created_at;
        scrollToBottom();
      }
    } catch (err) {
      showError(err.message);
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });

  // Send on Enter (but not Shift+Enter for newlines if textarea)
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });
}

// ── Mobile keyboard handling (visualViewport API) ──────────────────────────────

function setupVisualViewport() {
  if (!window.visualViewport) return;

  function onViewportChange() {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    const height = window.visualViewport.height;
    chatContainer.style.height = `${height}px`;
    scrollToBottom();
  }

  window.visualViewport.addEventListener('resize', onViewportChange);
  window.visualViewport.addEventListener('scroll', onViewportChange);
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function scrollToBottom() {
  const container = document.getElementById('messagesContainer');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function isScrolledToBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 50;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
