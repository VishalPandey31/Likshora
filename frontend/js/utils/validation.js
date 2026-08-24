/* =========================================================
   LIKSHORA — Form Validation Utilities
   Email, phone number and required field checkers
   ========================================================= */

window.Validation = {
  isValidEmail: function(email) {
    if (!email || typeof email !== 'string') return false;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email.trim());
  },

  isValidPhone: function(phone) {
    if (!phone) return false;
    const cleaned = String(phone).replace(/\D/g, '');
    if (cleaned.length === 10) return /^[6-9]\d{9}$/.test(cleaned) || /^\d{10}$/.test(cleaned);
    if (cleaned.length === 12 && cleaned.startsWith('91')) return true;
    if (cleaned.length === 11 && cleaned.startsWith('0')) return true;
    return false;
  },

  isNonEmpty: function(str) {
    return Boolean(str && String(str).trim().length > 0);
  }
};
