/* =========================================================
   LIKSHORA — OTP Verification Controller
   6-digit OTP digit box auto-focusing, 30s countdown timer & simulation
   ========================================================= */

(function() {
  const PENDING_SIGNUP_KEY = "rv_pending_signup";
  const PENDING_RESET_KEY = "rv_pending_reset";
  let countdownSeconds = 30;
  let timerInterval = null;

  function startResendTimer() {
    const timerText = document.getElementById("timerText");
    const resendBtn = document.getElementById("resendOtpBtn");

    if (!timerText || !resendBtn) return;

    countdownSeconds = 30;
    resendBtn.disabled = true;

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(function() {
      countdownSeconds -= 1;
      const formatted = countdownSeconds < 10 ? "0" + countdownSeconds : countdownSeconds;
      timerText.textContent = `(00:${formatted})`;

      if (countdownSeconds <= 0) {
        clearInterval(timerInterval);
        timerText.textContent = "";
        resendBtn.disabled = false;
      }
    }, 1000);
  }

  function initOtpDigits() {
    const boxes = document.querySelectorAll(".otp-digit-box");
    if (boxes.length === 0) return;

    boxes.forEach(function(box, index) {
      box.addEventListener("input", function(e) {
        const val = box.value.replace(/\D/g, "");
        box.value = val.slice(0, 1);

        if (val && index < boxes.length - 1) {
          boxes[index + 1].focus();
        }
      });

      box.addEventListener("keydown", function(e) {
        if (e.key === "Backspace" && !box.value && index > 0) {
          boxes[index - 1].focus();
        }
      });

      box.addEventListener("paste", function(e) {
        const paste = (e.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
        if (paste.length >= 6) {
          e.preventDefault();
          boxes.forEach(function(b, i) {
            b.value = paste[i] || "";
          });
          boxes[boxes.length - 1].focus();
        }
      });
    });
  }

  function initVerificationForm() {
    const form = document.getElementById("otpVerificationForm");
    if (!form) return;

    const pendingReset = window.StorageUtils ? window.StorageUtils.readJSON(PENDING_RESET_KEY, null) : null;
    const pendingSignup = window.StorageUtils ? window.StorageUtils.readJSON(PENDING_SIGNUP_KEY, null) : null;
    const emailEcho = document.getElementById("verifyEmailEcho");
    if (emailEcho) {
      if (pendingReset && pendingReset.identity) {
        emailEcho.textContent = pendingReset.identity;
      } else if (pendingSignup) {
        emailEcho.textContent = pendingSignup.email || pendingSignup.phone;
      }
    }

    startResendTimer();

    const resendBtn = document.getElementById("resendOtpBtn");
    if (resendBtn) {
      resendBtn.addEventListener("click", async function() {
        const targetEmail = (pendingSignup && pendingSignup.email) || (pendingReset && pendingReset.identity) || "";
        if (!targetEmail || !window.Validation || !window.Validation.isValidEmail(targetEmail)) {
          if (window.Toast) window.Toast.show("No valid email found to send verification link.");
          return;
        }

        resendBtn.disabled = true;
        try {
          const res = await window.AuthAPI.resendVerification(targetEmail);
          startResendTimer();
          if (res && res.success) {
            const successMsg = "Verification email sent to your registered email address.";
            if (window.Toast) window.Toast.show(successMsg);
          } else {
            const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
            const rawErr = res ? (res.error !== undefined && res.error !== null ? res.error : res.message) : null;
            const errMsg = String(normalizeFn ? normalizeFn(rawErr, "Failed to resend verification email.") : "Failed to resend verification email.");
            if (window.Toast) window.Toast.show(errMsg);
          }
        } catch (err) {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const errMsg = String(normalizeFn ? normalizeFn(err, "Failed to resend verification email.") : "Failed to resend verification email.");
          if (window.Toast) window.Toast.show(errMsg);
        }
      });
    }

    form.addEventListener("submit", function(e) {
      e.preventDefault();
      const boxes = document.querySelectorAll(".otp-digit-box");
      const enteredCode = Array.from(boxes).map(function(b) { return b.value; }).join("");

      if (enteredCode.length < 6) {
        if (window.Toast) window.Toast.show("Please enter all 6 digits.");
        return;
      }

      if (window.Toast) window.Toast.show("Verification successful!");
      setTimeout(function() {
        if (pendingReset && pendingReset.identity) {
          pendingReset.verified = true;
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(PENDING_RESET_KEY, pendingReset);
          }
          window.location.href = "reset-password.html";
        } else {
          window.location.href = "password-creation.html";
        }
      }, 500);
    });
  }

  async function checkEmailVerificationCallback() {
    const hash = window.location.hash || "";
    const search = window.location.search || "";
    const params = new URLSearchParams(search || (hash.startsWith("#") ? hash.substring(1) : hash));

    const accessToken = params.get("access_token") || params.get("token");
    const type = params.get("type");
    const verified = params.get("verified");

    if (accessToken || verified === "true" || type === "signup" || type === "email_verification" || type === "recovery") {
      if (window.Toast) {
        window.Toast.show("Email verification successful! Redirecting to login...");
      }

      if (accessToken && window.AuthAPI && window.AuthAPI.verifyEmail) {
        try {
          await window.AuthAPI.verifyEmail(accessToken);
        } catch (e) {}
      }

      setTimeout(function() {
        if (type === "recovery" || type === "recovery_password") {
          window.location.href = "reset-password.html" + search;
        } else {
          window.location.href = "login.html?verified=true";
        }
      }, 1500);
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    checkEmailVerificationCallback();
    initOtpDigits();
    initVerificationForm();
  });
})();
