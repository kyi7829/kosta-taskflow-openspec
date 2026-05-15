/**
 * auth.js — localStorage token management
 */

export const auth = {
  getToken() {
    return localStorage.getItem("token");
  },

  getUser() {
    try {
      const raw = localStorage.getItem("user");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setAuth(token, user) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  /**
   * Redirect to login if no token present.
   * Call at page load on protected pages.
   */
  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = "/index.html";
      return false;
    }
    return true;
  },

  /**
   * Redirect to kanban or team-select based on team_id.
   * Call on login/signup success.
   */
  redirectAfterLogin(user) {
    if (user.team_id) {
      window.location.href = `/kanban.html`;
    } else {
      window.location.href = "/team-select.html";
    }
  },
};

export default auth;
