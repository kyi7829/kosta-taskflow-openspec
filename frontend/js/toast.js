/**
 * toast.js — simple toast notification component
 */

let container = null;

function getContainer() {
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className =
      "fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none";
    document.body.appendChild(container);
  }
  return container;
}

/**
 * Show a toast notification.
 * @param {string} message  - Message text
 * @param {"error"|"success"|"info"} type
 * @param {number} duration - ms before auto-dismiss (default 4000)
 */
export function showToast(message, type = "error", duration = 4000) {
  const c = getContainer();
  const toast = document.createElement("div");

  const colorMap = {
    error: "bg-red-500 text-white",
    success: "bg-green-500 text-white",
    info: "bg-blue-500 text-white",
  };

  toast.className = `pointer-events-auto max-w-sm px-4 py-3 rounded-lg shadow-lg text-sm font-medium
    transition-all duration-300 opacity-0 translate-x-4
    ${colorMap[type] || colorMap.error}`;

  toast.textContent = message;
  c.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.remove("opacity-0", "translate-x-4");
    });
  });

  // Auto dismiss
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-x-4");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

export function showError(message) {
  showToast(message, "error");
}

export function showSuccess(message) {
  showToast(message, "success");
}

export default { showToast, showError, showSuccess };
