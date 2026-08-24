/* =========================================================
   LIKSHORA — Forgot Password Controller
   Reset request validation & pending session storage
   ========================================================= */

(function() {
  const PENDING_RESET_KEY = "rv_pending_reset";

  document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("forgotPasswordForm");
    if (!form) return;

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      const email = document.getElementById("resetIdentity").value.trim();

      if (!email) {
        if (window.Toast) window.Toast.show("Please enter your registered email address.");
        return;
      }

      if (window.Validation && !window.Validation.isValidEmail(email)) {
        if (window.Toast) window.Toast.show("Please enter a valid email address.");
        return;
      }

      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const res = await window.AuthAPI.resetPassword({ email: email });
        if (res && res.success) {
          if (window.Toast) window.Toast.show("Password recovery link sent! Check your inbox.");
          setTimeout(function() {
            window.location.href = "login.html";
          }, 1500);
        } else {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const rawErr = res ? (res.error !== undefined ? res.error : res.message) : null;
          const errMsg = normalizeFn ? normalizeFn(rawErr, "Failed to send reset link.") : "Failed to send reset link.";
          if (window.Toast) window.Toast.show(errMsg);
        }
      } catch (err) {
        const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
        const errMsg = normalizeFn ? normalizeFn(err, "Failed to send reset link.") : "Failed to send reset link.";
        if (window.Toast) window.Toast.show("Error: " + errMsg);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  });
})();
