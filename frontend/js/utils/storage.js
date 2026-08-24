/* =========================================================
   LIKSHORA — Storage Utilities
   LocalStorage wrapper with error boundaries
   ========================================================= */

window.StorageUtils = {
  readJSON: function(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw);
    } catch (e) {
      console.warn(`[StorageUtils] Error reading key "${key}":`, e);
      return fallback;
    }
  },

  writeJSON: function(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error(`[StorageUtils] Error writing key "${key}":`, e);
      return false;
    }
  },

  remove: function(key) {
    try {
      localStorage.removeItem(key);
    } catch (e) {
      console.error(`[StorageUtils] Error removing key "${key}":`, e);
    }
  }
};
