/* =========================================================
   LIKSHORA — Customer Signup Controller
   Frontend validation, password strength meter, eye toggles & storage
   ========================================================= */

(function() {
  const REGISTERED_USERS_KEY = "rv_registered_users";
  const CURRENT_USER_KEY = "rv_current_user";
  const CONFIG_USER_KEY = (window.RV_CONFIG && window.RV_CONFIG.STORAGE_KEYS && window.RV_CONFIG.STORAGE_KEYS.USER) || CURRENT_USER_KEY;

  function initEyeToggles() {
    document.querySelectorAll(".eye-toggle-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        const input = btn.previousElementSibling || btn.parentElement.querySelector("input");
        if (input) {
          const isPwd = input.type === "password";
          input.type = isPwd ? "text" : "password";
          btn.textContent = isPwd ? "🙈" : "👁️";
          btn.setAttribute("aria-label", isPwd ? "Hide password" : "Show password");
        }
      });
    });
  }

  function initPasswordStrength() {
    document.querySelectorAll("#signupPassword").forEach(function(pwdInput) {
      const form = pwdInput.closest("form");
      const strengthFill = form ? form.querySelector("#strengthBarFill") : document.getElementById("strengthBarFill");

      if (pwdInput && strengthFill) {
        pwdInput.addEventListener("input", function() {
          const val = pwdInput.value;
          if (!val) {
            strengthFill.style.width = "0%";
            return;
          }

          let score = 0;
          if (val.length >= 6) score += 33;
          if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score += 34;
          if (/[^A-Za-z0-9]/.test(val)) score += 33;

          strengthFill.style.width = Math.min(score, 100) + "%";
          if (score <= 33) strengthFill.style.background = "var(--rust)";
          else if (score <= 67) strengthFill.style.background = "var(--gold)";
          else strengthFill.style.background = "var(--success)";
        });
      }
    });
  }

  const PENDING_SIGNUP_KEY = "rv_pending_signup";

  function getAuthRedirectPath(targetPage) {
    const path = window.location.pathname;
    if (path.includes("/pages/auth/")) {
      return targetPage;
    } else if (path.includes("/pages/customer/")) {
      return "../auth/" + targetPage;
    } else {
      return "pages/auth/" + targetPage;
    }
  }

  function clearErrors(form) {
    if (!form) return;
    form.querySelectorAll(".input-error").forEach(function(el) {
      el.classList.remove("input-error");
    });
  }

  function initSignupForm() {
    const forms = document.querySelectorAll("#signupForm, #signupStep1Form");
    if (!forms.length) return;

    forms.forEach(function(form) {
      form.querySelectorAll(".auth-input, input").forEach(function(input) {
        input.addEventListener("input", function() {
          input.classList.remove("input-error");
        });
      });

      form.addEventListener("submit", async function(e) {
        e.preventDefault();
        clearErrors(form);

        const nameEl = form.querySelector("#signupName") || document.getElementById("signupName");
        const emailEl = form.querySelector("#signupEmail") || document.getElementById("signupEmail");
        const phoneEl = form.querySelector("#signupPhone") || document.getElementById("signupPhone");
        const pwdEl = form.querySelector("#signupPassword") || document.getElementById("signupPassword");
        const confirmPwdEl = form.querySelector("#signupConfirmPassword") || document.getElementById("signupConfirmPassword");

        const name = nameEl ? nameEl.value.trim() : "";
        const email = emailEl ? emailEl.value.trim() : "";
        const phone = phoneEl ? phoneEl.value.trim() : "";
        const password = pwdEl ? pwdEl.value : "";
        const confirmPassword = confirmPwdEl ? confirmPwdEl.value : "";

        let firstInvalid = null;
        let missingFields = false;

        if (!name && nameEl) {
          nameEl.classList.add("input-error");
          if (!firstInvalid) firstInvalid = nameEl;
          missingFields = true;
        }
        if (!email && emailEl) {
          emailEl.classList.add("input-error");
          if (!firstInvalid) firstInvalid = emailEl;
          missingFields = true;
        }
        if (!phone && phoneEl) {
          phoneEl.classList.add("input-error");
          if (!firstInvalid) firstInvalid = phoneEl;
          missingFields = true;
        }
        if (pwdEl && !password) {
          pwdEl.classList.add("input-error");
          if (!firstInvalid) firstInvalid = pwdEl;
          missingFields = true;
        }

        if (missingFields) {
          if (window.Toast) window.Toast.show("Please fill out all required fields.");
          if (firstInvalid) firstInvalid.focus();
          return;
        }

        if (window.Validation && !window.Validation.isValidEmail(email)) {
          if (emailEl) emailEl.classList.add("input-error");
          if (window.Toast) window.Toast.show("Please enter a valid email address.");
          if (emailEl) emailEl.focus();
          return;
        }

        if (phone && window.Validation && !window.Validation.isValidPhone(phone)) {
          if (phoneEl) phoneEl.classList.add("input-error");
          if (window.Toast) window.Toast.show("Please enter a valid 10-digit mobile number.");
          if (phoneEl) phoneEl.focus();
          return;
        }

        if (pwdEl) {
          if (password.length < 8) {
            pwdEl.classList.add("input-error");
            if (window.Toast) window.Toast.show("Password must be at least 8 characters long.");
            pwdEl.focus();
            return;
          }
          if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
            pwdEl.classList.add("input-error");
            if (window.Toast) window.Toast.show("Password must contain both letters and numbers.");
            pwdEl.focus();
            return;
          }
          if (confirmPwdEl && password !== confirmPassword) {
            confirmPwdEl.classList.add("input-error");
            if (window.Toast) window.Toast.show("Passwords do not match.");
            confirmPwdEl.focus();
            return;
          }
        }

        if (!pwdEl) {
          const pendingUser = { name, email, phone };
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(PENDING_SIGNUP_KEY, pendingUser);
          }
          if (window.Toast) window.Toast.show("Proceeding to verification...");
          setTimeout(function() {
            window.location.href = getAuthRedirectPath("email-verification.html");
          }, 500);
          return;
        }

        const submitBtn = form.querySelector("button[type='submit']");
        if (submitBtn) submitBtn.disabled = true;

        try {
          const res = await window.AuthAPI.signup({
            name: name,
            email: email,
            phone: phone,
            password: password
          });

          if (res && res.success) {
            const successMsg = `Account created. Please check your email to verify your account.`;
            if (window.Toast) {
              window.Toast.show(successMsg);
            }
            if (window.StorageUtils) {
              window.StorageUtils.writeJSON(PENDING_SIGNUP_KEY, { name, email, phone });
            }
            setTimeout(function() {
              window.location.href = getAuthRedirectPath("login.html") + "?registered_email=" + encodeURIComponent(email) + "&unverified=true";
            }, 2000);
          } else {
            const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
            const rawErr = res ? (res.error !== undefined && res.error !== null ? res.error : res.message) : null;
            const errMsg = String(normalizeFn ? normalizeFn(rawErr, "Signup failed. Please check details and try again.") : "Signup failed. Please check details and try again.");
            if (window.Toast) window.Toast.show(errMsg);
            const lowerMsg = errMsg.toLowerCase();
            if (emailEl && (lowerMsg.includes("email") || lowerMsg.includes("user"))) {
              emailEl.classList.add("input-error");
            }
            if (phoneEl && (lowerMsg.includes("phone") || lowerMsg.includes("mobile"))) {
              phoneEl.classList.add("input-error");
            }
          }
        } catch (err) {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const errMsg = String(normalizeFn ? normalizeFn(err, "Signup failed due to a network error.") : "Signup failed due to a network error.");
          if (window.Toast) window.Toast.show(errMsg);
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    });
  }

  function initPasswordCreationForm() {
    const form = document.getElementById("passwordCreationForm");
    if (!form) return;

    form.querySelectorAll(".auth-input, input").forEach(function(input) {
      input.addEventListener("input", function() {
        input.classList.remove("input-error");
      });
    });

    form.addEventListener("submit", async function(e) {
      e.preventDefault();
      clearErrors(form);

      const pwdEl = document.getElementById("newPassword") || document.getElementById("signupPassword");
      const confirmPwdEl = document.getElementById("confirmPassword") || document.getElementById("signupConfirmPassword");

      const password = pwdEl ? pwdEl.value : "";
      const confirmPassword = confirmPwdEl ? confirmPwdEl.value : "";

      if (!password || !confirmPassword) {
        if (!password && pwdEl) pwdEl.classList.add("input-error");
        if (!confirmPassword && confirmPwdEl) confirmPwdEl.classList.add("input-error");
        if (window.Toast) window.Toast.show("Please enter and confirm your new password.");
        if (!password && pwdEl) pwdEl.focus();
        else if (!confirmPassword && confirmPwdEl) confirmPwdEl.focus();
        return;
      }

      if (password.length < 8) {
        if (pwdEl) pwdEl.classList.add("input-error");
        if (window.Toast) window.Toast.show("Password must be at least 8 characters long.");
        if (pwdEl) pwdEl.focus();
        return;
      }

      if (password !== confirmPassword) {
        if (confirmPwdEl) confirmPwdEl.classList.add("input-error");
        if (window.Toast) window.Toast.show("Passwords do not match. Please enter matching passwords.");
        if (confirmPwdEl) confirmPwdEl.focus();
        return;
      }

      const pending = window.StorageUtils ? window.StorageUtils.readJSON(PENDING_SIGNUP_KEY, null) : null;
      const email = pending ? pending.email : "";
      const name = pending ? pending.name : "";
      const phone = pending ? pending.phone : "";

      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const res = await window.AuthAPI.signup({
          name: name,
          email: email,
          phone: phone,
          password: password
        });

        if (res && res.success) {
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(PENDING_SIGNUP_KEY, null);
          }
          if (window.Toast) window.Toast.show("Account created successfully. Please verify your email before logging in.");
          setTimeout(function() {
            window.location.href = getAuthRedirectPath("login.html");
          }, 1500);
        } else {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const rawErr = res ? (res.error !== undefined && res.error !== null ? res.error : res.message) : null;
          const errMsg = String(normalizeFn ? normalizeFn(rawErr, "Signup failed. Please try again.") : "Signup failed. Please try again.");
          if (window.Toast) window.Toast.show(errMsg);
        }
      } catch (err) {
        const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
        const errMsg = String(normalizeFn ? normalizeFn(err, "Signup failed due to a network error.") : "Signup failed due to a network error.");
        if (window.Toast) window.Toast.show(errMsg);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    initEyeToggles();
    initPasswordStrength();
    initSignupForm();
    initPasswordCreationForm();
  });
})();
