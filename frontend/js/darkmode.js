// 초기화 — localStorage에서 복원 (깜빡임 방지 스크립트와 별개로 버튼 상태 동기화)
function initDarkMode() {
  const isDark = document.documentElement.classList.contains('dark');
  updateIcon(isDark);
}

function toggleDarkMode() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  updateIcon(isDark);
}

function updateIcon(isDark) {
  const btns = document.querySelectorAll('.dark-toggle-btn');
  btns.forEach(btn => { btn.textContent = isDark ? '☀️' : '🌙'; });
}

export { initDarkMode, toggleDarkMode };
