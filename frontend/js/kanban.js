/**
 * kanban.js — Kanban board logic with drag & drop
 */
import api from './api.js';
import { showError, showSuccess } from './toast.js';
import auth from './auth.js';

const STATUSES = ['TODO', 'DOING', 'DONE'];
const STATUS_LABELS = { TODO: '할 일', DOING: '진행 중', DONE: '완료' };
const STATUS_COLORS = {
  TODO: 'bg-gray-100',
  DOING: 'bg-blue-100',
  DONE: 'bg-green-100',
};

let allTasks = [];
let currentFilter = 'all';
let currentUser = null;
let teamInfo = null;
let members = [];
let dragTaskId = null;

// ── Mobile swipe state ───────────────────────────────────────────────────────
let mobileColumnIndex = 0;
let touchStartX = 0;

export async function initKanban() {
  currentUser = auth.getUser();
  if (!currentUser || !currentUser.team_id) {
    window.location.href = '/team-select.html';
    return;
  }

  await loadTeamInfo();
  await loadMembers();
  await loadTasks();
  setupFilterButtons();
  setupAddTaskButtons();
  setupMobileSwipe();
  renderMobileTabIndicator();
}

async function loadTeamInfo() {
  try {
    teamInfo = await api.get(`/teams/${currentUser.team_id}`);
    document.getElementById('teamName').textContent = teamInfo.name;
    document.getElementById('inviteCodeDisplay').textContent = teamInfo.invite_code;
  } catch (err) {
    showError(err.message);
  }
}

async function loadMembers() {
  try {
    members = await api.get(`/teams/${currentUser.team_id}/members`);
    renderMembersPanel();
  } catch (err) {
    showError(err.message);
  }
}

async function loadTasks() {
  try {
    let path = `/teams/${currentUser.team_id}/tasks`;
    if (currentFilter === 'me') path += '?filter=me';
    else if (currentFilter === 'unassigned') path += '?filter=unassigned';
    allTasks = await api.get(path);
    renderBoard();
  } catch (err) {
    showError(err.message);
  }
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function renderBoard() {
  STATUSES.forEach(status => {
    const col = document.getElementById(`col-${status}`);
    if (!col) return;
    const tasksForCol = allTasks.filter(t => t.status === status);
    col.innerHTML = '';
    tasksForCol.forEach(task => {
      col.appendChild(createTaskCard(task));
    });

    // Update count
    const countEl = col.closest('.kanban-column')?.querySelector('.task-count');
    if (countEl) countEl.textContent = tasksForCol.length;
  });
}

function getMemberEmail(userId) {
  if (!userId) return null;
  const m = members.find(m => m.id === userId);
  return m ? m.email.split('@')[0] : `#${userId}`;
}

function createTaskCard(task) {
  const card = document.createElement('div');
  card.className = 'task-card bg-white rounded-lg p-3 shadow-sm border border-gray-200 cursor-grab hover:shadow-md transition-shadow mb-2';
  card.dataset.taskId = task.id;
  card.draggable = true;

  const assigneeLabel = task.assignee_id
    ? `<span class="text-xs text-indigo-600 font-medium">@${getMemberEmail(task.assignee_id)}</span>`
    : `<span class="text-xs text-gray-400">미할당</span>`;

  card.innerHTML = `
    <p class="text-sm font-medium text-gray-800 mb-2 leading-snug">${escapeHtml(task.title)}</p>
    <div class="flex items-center justify-between">
      ${assigneeLabel}
      <button class="delete-task-btn text-gray-300 hover:text-red-500 text-xs transition-colors" data-task-id="${task.id}" title="삭제">✕</button>
    </div>
  `;

  // Click to open modal
  card.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-task-btn')) return;
    openTaskModal(task.id);
  });

  // Delete button
  card.querySelector('.delete-task-btn').addEventListener('click', async (e) => {
    e.stopPropagation();
    if (!confirm('이 태스크를 삭제할까요?')) return;
    await deleteTask(task.id);
  });

  // Drag events
  card.addEventListener('dragstart', (e) => {
    dragTaskId = task.id;
    card.classList.add('opacity-50');
    e.dataTransfer.effectAllowed = 'move';
  });

  card.addEventListener('dragend', () => {
    card.classList.remove('opacity-50');
    dragTaskId = null;
  });

  return card;
}

// ── Drag & Drop columns ───────────────────────────────────────────────────────

export function setupDropZones() {
  STATUSES.forEach(status => {
    const col = document.getElementById(`col-${status}`);
    if (!col) return;

    col.addEventListener('dragover', (e) => {
      e.preventDefault();
      col.classList.add('bg-blue-50', 'ring-2', 'ring-indigo-300');
      e.dataTransfer.dropEffect = 'move';
    });

    col.addEventListener('dragleave', (e) => {
      if (!col.contains(e.relatedTarget)) {
        col.classList.remove('bg-blue-50', 'ring-2', 'ring-indigo-300');
      }
    });

    col.addEventListener('drop', async (e) => {
      e.preventDefault();
      col.classList.remove('bg-blue-50', 'ring-2', 'ring-indigo-300');
      if (dragTaskId) {
        await updateTaskStatus(dragTaskId, status);
      }
    });
  });
}

async function updateTaskStatus(taskId, newStatus) {
  const task = allTasks.find(t => t.id === taskId);
  if (!task || task.status === newStatus) return;
  try {
    const updated = await api.patch(`/tasks/${taskId}/status`, { status: newStatus });
    const idx = allTasks.findIndex(t => t.id === taskId);
    if (idx !== -1) allTasks[idx] = updated;
    renderBoard();
  } catch (err) {
    showError(err.message);
  }
}

// ── Task Modal ─────────────────────────────────────────────────────────────────

function openTaskModal(taskId) {
  const task = allTasks.find(t => t.id === taskId);
  if (!task) return;

  const modal = document.getElementById('taskModal');
  document.getElementById('modalTitle').value = task.title;
  document.getElementById('modalStatus').value = task.status;

  // Populate assignee select
  const assigneeSelect = document.getElementById('modalAssignee');
  assigneeSelect.innerHTML = '<option value="">미할당</option>';
  members.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.email;
    if (task.assignee_id === m.id) opt.selected = true;
    assigneeSelect.appendChild(opt);
  });

  // Show/hide delete button based on permissions
  const deleteBtn = document.getElementById('modalDeleteBtn');
  const isOwner = teamInfo && teamInfo.owner_id === currentUser.id;
  const isCreator = task.creator_id === currentUser.id;
  deleteBtn.style.display = (isOwner || isCreator) ? 'block' : 'none';

  modal.dataset.taskId = taskId;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeTaskModal() {
  const modal = document.getElementById('taskModal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

export function setupTaskModal() {
  document.getElementById('modalCloseBtn').addEventListener('click', closeTaskModal);
  document.getElementById('taskModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('taskModal')) closeTaskModal();
  });

  document.getElementById('modalSaveBtn').addEventListener('click', async () => {
    const modal = document.getElementById('taskModal');
    const taskId = parseInt(modal.dataset.taskId);
    const title = document.getElementById('modalTitle').value.trim();
    const status = document.getElementById('modalStatus').value;
    const assigneeId = document.getElementById('modalAssignee').value
      ? parseInt(document.getElementById('modalAssignee').value)
      : null;

    if (!title) {
      showError('제목을 입력해주세요');
      return;
    }

    try {
      const task = allTasks.find(t => t.id === taskId);
      // Update title & assignee
      const updated = await api.put(`/tasks/${taskId}`, { title, assignee_id: assigneeId });
      // Update status if changed
      if (task && task.status !== status) {
        await api.patch(`/tasks/${taskId}/status`, { status });
        updated.status = status;
      }
      const idx = allTasks.findIndex(t => t.id === taskId);
      if (idx !== -1) allTasks[idx] = updated;
      renderBoard();
      closeTaskModal();
      showSuccess('태스크가 수정됐습니다');
    } catch (err) {
      showError(err.message);
    }
  });

  document.getElementById('modalDeleteBtn').addEventListener('click', async () => {
    const modal = document.getElementById('taskModal');
    const taskId = parseInt(modal.dataset.taskId);
    if (!confirm('이 태스크를 삭제할까요?')) return;
    await deleteTask(taskId);
    closeTaskModal();
  });
}

async function deleteTask(taskId) {
  try {
    await api.delete(`/tasks/${taskId}`);
    allTasks = allTasks.filter(t => t.id !== taskId);
    renderBoard();
    showSuccess('삭제됐습니다');
  } catch (err) {
    showError(err.message);
  }
}

// ── Filter buttons ─────────────────────────────────────────────────────────────

function setupFilterButtons() {
  const btns = document.querySelectorAll('[data-filter]');
  btns.forEach(btn => {
    btn.addEventListener('click', async () => {
      currentFilter = btn.dataset.filter;
      btns.forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('bg-gray-100', 'text-gray-700');
      });
      btn.classList.remove('bg-gray-100', 'text-gray-700');
      btn.classList.add('bg-indigo-600', 'text-white');
      await loadTasks();
    });
  });
}

// ── Add task inline ─────────────────────────────────────────────────────────────

function setupAddTaskButtons() {
  STATUSES.forEach(status => {
    const btn = document.getElementById(`addTask-${status}`);
    if (!btn) return;
    btn.addEventListener('click', () => showAddTaskForm(status));
  });
}

function showAddTaskForm(status) {
  const col = document.getElementById(`col-${status}`);
  // Remove existing forms
  document.querySelectorAll('.add-task-form').forEach(f => f.remove());

  const form = document.createElement('div');
  form.className = 'add-task-form bg-white rounded-lg p-3 shadow-sm border-2 border-indigo-300 mb-2';
  form.innerHTML = `
    <textarea
      class="w-full text-sm border-none outline-none resize-none text-gray-800 placeholder-gray-400"
      placeholder="태스크 제목 입력..."
      rows="2"
      maxlength="100"
    ></textarea>
    <div class="flex gap-2 mt-2">
      <button class="confirm-add-btn bg-indigo-600 text-white text-xs py-1 px-3 rounded hover:bg-indigo-700">추가</button>
      <button class="cancel-add-btn text-gray-500 text-xs py-1 px-3 rounded hover:bg-gray-100">취소</button>
    </div>
  `;

  col.insertBefore(form, col.firstChild);
  form.querySelector('textarea').focus();

  form.querySelector('.confirm-add-btn').addEventListener('click', async () => {
    const title = form.querySelector('textarea').value.trim();
    if (!title) { showError('제목을 입력해주세요'); return; }
    try {
      const newTask = await api.post(`/teams/${currentUser.team_id}/tasks`, { title, assignee_id: null });
      // Force status to the target column
      if (status !== 'TODO') {
        await api.patch(`/tasks/${newTask.id}/status`, { status });
        newTask.status = status;
      }
      allTasks.unshift(newTask);
      form.remove();
      renderBoard();
    } catch (err) {
      showError(err.message);
    }
  });

  form.querySelector('.cancel-add-btn').addEventListener('click', () => form.remove());
  form.querySelector('textarea').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') form.remove();
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.querySelector('.confirm-add-btn').click();
    }
  });
}

// ── Members Panel ──────────────────────────────────────────────────────────────

function renderMembersPanel() {
  const panel = document.getElementById('membersPanel');
  if (!panel) return;

  panel.innerHTML = '';
  members.forEach(m => {
    const div = document.createElement('div');
    div.className = 'flex items-center gap-2 py-1.5';
    div.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-700">
        ${m.email[0].toUpperCase()}
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-gray-800 truncate">
          ${m.role === 'owner' ? '★ ' : ''}${escapeHtml(m.email.split('@')[0])}
        </p>
        <p class="text-xs text-gray-400 truncate">${escapeHtml(m.email)}</p>
      </div>
    `;
    panel.appendChild(div);
  });
}

// ── Mobile swipe ───────────────────────────────────────────────────────────────

function setupMobileSwipe() {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  board.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });

  board.addEventListener('touchend', (e) => {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0 && mobileColumnIndex < STATUSES.length - 1) {
        mobileColumnIndex++;
      } else if (diff < 0 && mobileColumnIndex > 0) {
        mobileColumnIndex--;
      }
      updateMobileView();
    }
  }, { passive: true });
}

function updateMobileView() {
  if (window.innerWidth >= 768) return;
  STATUSES.forEach((status, idx) => {
    const wrapper = document.getElementById(`wrapper-${status}`);
    if (wrapper) {
      wrapper.style.display = idx === mobileColumnIndex ? 'block' : 'none';
    }
  });
  renderMobileTabIndicator();
}

function renderMobileTabIndicator() {
  const indicator = document.getElementById('mobileTabIndicator');
  if (!indicator) return;

  indicator.innerHTML = STATUSES.map((status, idx) => `
    <button
      class="px-3 py-1 text-sm rounded-full font-medium transition-colors
        ${idx === mobileColumnIndex ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'}"
      data-idx="${idx}"
    >
      ${STATUS_LABELS[status]}
    </button>
  `).join('');

  indicator.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      mobileColumnIndex = parseInt(btn.dataset.idx);
      updateMobileView();
    });
  });
}

// ── Utils ──────────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Handle window resize for mobile
window.addEventListener('resize', () => {
  if (window.innerWidth >= 768) {
    // Show all columns on desktop
    STATUSES.forEach(status => {
      const wrapper = document.getElementById(`wrapper-${status}`);
      if (wrapper) wrapper.style.display = 'block';
    });
  } else {
    updateMobileView();
  }
});
