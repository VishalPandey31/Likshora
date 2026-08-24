/* =========================================================
   LIKSHORA — Formatting Utilities
   Currency, text sanitizer & initial extractors
   ========================================================= */

window.Formatters = {
  formatINR: function(amount) {
    const num = Number(amount) || 0;
    const symbol = window.RV_CONFIG ? window.RV_CONFIG.CURRENCY_SYMBOL : "₹";
    const locale = window.RV_CONFIG ? window.RV_CONFIG.LOCALE : "en-IN";
    return symbol + num.toLocaleString(locale);
  },

  escapeHTML: function(str) {
    return String(str ?? "").replace(/[&<>"']/g, function(c) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[c];
    });
  },

  getInitials: function(name) {
    if (!name) return "?";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  },

  formatProductImage: function(imgInput, isSubpage) {
    let src = imgInput;
    if (src && typeof src === "object") src = src.url;
    if (!src) return "";
    src = String(src).trim();

    // Data URLs, HTTP/HTTPS, and Blob URLs are absolute
    if (src.startsWith("data:") || src.startsWith("http://") || src.startsWith("https://") || src.startsWith("blob:")) {
      return src;
    }

    // Relative path handling
    if (isSubpage) {
      if (!src.startsWith("../")) {
        if (src.startsWith("/")) src = "../.." + src;
        else src = "../../" + src;
      }
    } else {
      // Root page
      if (src.startsWith("../../")) {
        src = src.replace("../../", "");
      } else if (src.startsWith("../")) {
        src = src.replace("../", "");
      }
    }
    return src;
  }
};
