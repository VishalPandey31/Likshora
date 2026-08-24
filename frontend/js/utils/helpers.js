/* =========================================================
   LIKSHORA — Helpers Utilities
   ID generators, debouncers and DOM utility helpers
   ========================================================= */

window.Helpers = {
  uid: function(prefix) {
    const p = prefix || "rv";
    return p + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  },

  debounce: function(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait || 250);
    };
  },

  scrollToElement: function(element, offset) {
    if (!element) return;
    const top = element.getBoundingClientRect().top + window.pageYOffset - (offset || 100);
    window.scrollTo({ top: top, behavior: 'smooth' });
  },

  normalizeError: function(error, defaultMsg) {
    const fallback = defaultMsg || "An unexpected error occurred. Please try again.";
    if (error === undefined || error === null) return String(fallback);
    if (typeof error === "string") return String(error.trim() || fallback);
    if (typeof error === "number" || typeof error === "boolean") return String(error);
    if (error instanceof Error && error.message) return String(error.message);

    if (typeof error === "object") {
      if (error.message && typeof error.message === "string") return String(error.message);
      if (error.error) {
        if (typeof error.error === "string") return String(error.error);
        if (typeof error.error === "object") {
          if (error.error.message && typeof error.error.message === "string") return String(error.error.message);
          if (error.error.msg && typeof error.error.msg === "string") return String(error.error.msg);
          if (error.error.description && typeof error.error.description === "string") return String(error.error.description);
          if (error.error.error_description && typeof error.error.error_description === "string") return String(error.error.error_description);
        }
      }
      if (error.msg && typeof error.msg === "string") return String(error.msg);
      if (error.error_description && typeof error.error_description === "string") return String(error.error_description);
      if (error.details && typeof error.details === "string") return String(error.details);
      if (error.detail && typeof error.detail === "string") return String(error.detail);

      try {
        const jsonStr = JSON.stringify(error);
        if (jsonStr && jsonStr !== "{}" && !jsonStr.includes("[object Object]")) {
          return jsonStr;
        }
      } catch (e) {}
    }

    try {
      const str = String(error);
      if (str && str !== "[object Object]") return str;
    } catch (e) {}

    return String(fallback);
  }
};

window.normalizeAuthError = function(error, defaultMsg) {
  return window.Helpers.normalizeError(error, defaultMsg);
};


