/* =========================================================
   LIKSHORA — App Configuration
   Storage keys, default fallback state & global constants
   ========================================================= */

window.RV_CONFIG = {
  // ──────────────────────────────────────────────────────────
  // API_BASE_URL: Points to your backend server.
  //   • Locally  → http://127.0.0.1:5000
  //   • Production → Your Render backend URL (e.g. https://likshora-api.onrender.com)
  // ──────────────────────────────────────────────────────────
  API_BASE_URL: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.hostname === "")
    ? "http://127.0.0.1:5000"
    : "https://likshora-api.onrender.com",  // ← CHANGE THIS to your actual Render backend URL after deployment

  // ──────────────────────────────────────────────────────────
  // Razorpay Publishable Key (safe to expose in frontend)
  //   • Test mode → rzp_test_XXXXXXXXXX
  //   • Live mode → rzp_live_XXXXXXXXXX (switch after KYC)
  // ──────────────────────────────────────────────────────────
  RAZORPAY_KEY_ID: "rzp_test_TTBpNyeq3F4cfi",  // ← CHANGE to rzp_live_... after Razorpay KYC

  // Shared LocalStorage keys (syncs storefront & admin panel)
  STORAGE_KEYS: {
    PRODUCTS: "rv_products",
    HERO: "rv_hero_images",
    MARQUEE: "rv_marquee_images",
    ORDERS: "rv_orders",
    LOGINS: "rv_logins",
    USER: "rv_current_user",
    TOKEN: "rv_access_token",
    REFRESH_TOKEN: "rv_refresh_token"
  },

  // Currency & Locale Constants
  CURRENCY_SYMBOL: "₹",
  LOCALE: "en-IN",

  // Default Products Collection
  DEFAULT_PRODUCTS: []
};
