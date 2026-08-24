/* =========================================================
   LIKSHORA — Reset Password Controller
   Extract recovery token, validate password complexity & update Supabase credentials
   ========================================================= */

(function() {
  document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("resetPasswordForm");
    if (!form) return;

    const hash = window.location.hash || "";
    const search = window.location.search || "";
    const params = new URLSearchParams(search || (hash.startsWith("#") ? hash.substring(1) : hash));

    const accessToken = params.get("access_token") || params.get("token");

    const pwdInput = document.getElementById("resetNewPassword");
    const confirmInput = document.getElementById("resetConfirmPassword");
    const strengthFill = document.getElementById("resetStrengthFill");
    const toggleBtns = document.querySelectorAll(".eye-toggle-btn");

    toggleBtns.forEach(function(btn) {
      btn.addEventListener("click", function() {
        const input = btn.previousElementSibling || btn.parentElement.querySelector("input");
        if (input) {
          const type = input.type === "password" ? "text" : "password";
          input.type = type;
          btn.textContent = type === "password" ? "👁️" : "🙈";
        }
      });
    });

    if (pwdInput && strengthFill) {
      pwdInput.addEventListener("input", function() {
        const val = pwdInput.value;
        let score = 0;
        if (val.length >= 8) score += 33;
        if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score += 34;
        if (/[^A-Za-z0-9]/.test(val)) score += 33;

        strengthFill.style.width = Math.min(score, 100) + "%";
        if (score <= 33) strengthFill.style.background = "var(--rust)";
        else if (score <= 67) strengthFill.style.background = "var(--gold)";
        else strengthFill.style.background = "var(--success)";
      });
    }

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      const pwd = pwdInput ? pwdInput.value : "";
      const confirmPwd = confirmInput ? confirmInput.value : "";

      if (!pwd || pwd.length < 8) {
        if (window.Toast) window.Toast.show("Password must be at least 8 characters long.");
        if (pwdInput) pwdInput.focus();
        return;
      }

      if (!/[A-Za-z]/.test(pwd) || !/[0-9]/.test(pwd)) {
        if (window.Toast) window.Toast.show("Password must contain both letters and numbers.");
        if (pwdInput) pwdInput.focus();
        return;
      }

      if (pwd !== confirmPwd) {
        if (window.Toast) window.Toast.show("Passwords do not match. Please re-enter matching passwords.");
        if (confirmInput) confirmInput.focus();
        return;
      }

      if (!accessToken) {
        if (window.Toast) window.Toast.show("Invalid or expired password reset link. Please request a new recovery link.");
        setTimeout(function() {
          window.location.href = "forgot-password.html";
        }, 2000);
        return;
      }

      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const res = await window.AuthAPI.updatePassword({
          access_token: accessToken,
          password: pwd
        });

        if (res && res.success) {
          if (window.Toast) window.Toast.show("Password updated successfully! You can now log in.");
          setTimeout(function() {
            window.location.href = "login.html";
          }, 1500);
        } else {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const rawErr = res ? (res.error !== undefined && res.error !== null ? res.error : res.message) : null;
          const errMsg = String(normalizeFn ? normalizeFn(rawErr, "Failed to update password. Please try again.") : "Failed to update password. Please try again.");
          if (window.Toast) window.Toast.show(errMsg);
        }
      } catch (err) {
        const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
        const errMsg = String(normalizeFn ? normalizeFn(err, "Failed to update password.") : "Failed to update password.");
        if (window.Toast) window.Toast.show(errMsg);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  });
})();

