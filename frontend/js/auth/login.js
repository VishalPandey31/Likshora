/* =========================================================
   LIKSHORA — Customer Login Controller
   Tab switching (Mobile OTP / Email Password), credential validation & session creation
   ========================================================= */

(function() {
  const REGISTERED_USERS_KEY = "rv_registered_users";
  const CURRENT_USER_KEY = "rv_current_user";
  const CONFIG_USER_KEY = (window.RV_CONFIG && window.RV_CONFIG.STORAGE_KEYS && window.RV_CONFIG.STORAGE_KEYS.USER) || CURRENT_USER_KEY;

  function clearErrors(form) {
    if (!form) return;
    form.querySelectorAll(".input-error").forEach(function(el) {
      el.classList.remove("input-error");
    });
  }

  function initLoginTabs() {
    const tabOtp = document.getElementById("tabLoginOtp");
    const tabEmail = document.getElementById("tabLoginEmail");
    const formOtp = document.getElementById("loginFormOtp");
    const formEmail = document.getElementById("loginFormEmail");

    if (!tabOtp || !tabEmail || !formOtp || !formEmail) return;

    tabOtp.addEventListener("click", function() {
      tabOtp.classList.add("active");
      tabEmail.classList.remove("active");
      formOtp.classList.remove("hidden");
      formEmail.classList.add("hidden");
    });

    tabEmail.addEventListener("click", function() {
      tabEmail.classList.add("active");
      tabOtp.classList.remove("active");
      formEmail.classList.remove("hidden");
      formOtp.classList.add("hidden");
    });
  }

  const EYE_OPEN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
  const EYE_OFF_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

  function initEyeToggles() {
    document.querySelectorAll(".eye-toggle-btn").forEach(function(btn) {
      if (!btn.querySelector("svg")) {
        btn.innerHTML = EYE_OPEN_SVG;
      }
      btn.addEventListener("click", function() {
        const input = btn.previousElementSibling || btn.parentElement.querySelector("input");
        if (input) {
          const isPwd = input.type === "password";
          input.type = isPwd ? "text" : "password";
          btn.innerHTML = isPwd ? EYE_OFF_SVG : EYE_OPEN_SVG;
          btn.setAttribute("aria-label", isPwd ? "Hide password" : "Show password");
        }
      });
    });
  }

  function showResendVerificationUI(form, targetEmail, customMsg) {
    if (!form) return;
    let container = form.querySelector(".unverified-notice-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "unverified-notice-container";
      container.style.cssText = "margin-top: 1.2em; padding: 1em; background: rgba(184, 80, 66, 0.08); border: 1px solid var(--rust, #b85042); border-radius: 8px; text-align: center;";
      form.appendChild(container);
    }

    const msgToDisplay = customMsg || "Please verify your email before logging in.";
    const safeEmail = window.Formatters ? window.Formatters.escapeHTML(targetEmail) : targetEmail;
    container.innerHTML = `
      <p style="margin: 0 0 0.6em; font-size: 0.86rem; color: var(--rust, #b85042); font-weight: 500;">
        ${window.Formatters ? window.Formatters.escapeHTML(msgToDisplay) : msgToDisplay}
      </p>
      <p style="margin: 0 0 0.8em; font-size: 0.8rem; color: var(--ink-soft, #555);">
        Verification email sent to <strong>${safeEmail}</strong>
      </p>
      <button type="button" class="btn-resend-verification btn btn-secondary btn-sm" style="padding: 0.4em 1em; font-size: 0.82rem; cursor: pointer;">
        Resend Verification Email
      </button>
    `;

    const resendBtn = container.querySelector(".btn-resend-verification");
    if (resendBtn) {
      resendBtn.onclick = async function() {
        resendBtn.disabled = true;
        resendBtn.textContent = "Sending...";
        try {
          const res = await window.AuthAPI.resendVerification(targetEmail);
          if (res && res.success) {
            const successMsg = (res.data && res.data.message) || res.message || `Verification email has been sent again to ${targetEmail}.`;
            if (window.Toast) window.Toast.show(successMsg);
            const noticeP = container.querySelector("p");
            if (noticeP) noticeP.textContent = successMsg;
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
        } finally {
          resendBtn.disabled = false;
          resendBtn.textContent = "Resend Verification Email";
        }
      };
    }
  }

  function checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const registeredEmail = params.get("registered_email");
    const isUnverified = params.get("unverified") === "true";
    const isVerified = params.get("verified") === "true";

    const emailEl = document.querySelector("#loginEmail, input[type='email']");
    if (registeredEmail && emailEl) {
      emailEl.value = registeredEmail;
    }

    const form = document.querySelector("#loginFormEmail, #loginForm");
    if (isUnverified && registeredEmail && form) {
      showResendVerificationUI(form, registeredEmail, "Account created successfully. Please check your email and verify your account before logging in.");
      if (window.Toast) window.Toast.show(`Verification email sent to ${registeredEmail}. Please verify before logging in.`);
    } else if (isVerified) {
      if (window.Toast) window.Toast.show("Email verified successfully! You can now log in.");
    }
  }

  function initForms() {
    const loginForms = document.querySelectorAll("#loginFormEmail, #loginForm");

    loginForms.forEach(function(form) {
      form.querySelectorAll("input").forEach(function(input) {
        input.addEventListener("input", function() {
          input.classList.remove("input-error");
        });
      });

      form.addEventListener("submit", async function(e) {
        e.preventDefault();
        clearErrors(form);

        const emailEl = form.querySelector("#loginEmail, input[type='email']");
        const pwdEl = form.querySelector("#loginPassword, input[type='password']");
        const email = emailEl ? emailEl.value.trim() : "";
        const pwd = pwdEl ? pwdEl.value : "";

        if (!email || !pwd) {
          if (!email && emailEl) emailEl.classList.add("input-error");
          if (!pwd && pwdEl) pwdEl.classList.add("input-error");
          if (window.Toast) window.Toast.show("Please enter both email address and password.");
          if (!email && emailEl) emailEl.focus();
          else if (!pwd && pwdEl) pwdEl.focus();
          return;
        }

        if (window.Validation && !window.Validation.isValidEmail(email)) {
          if (emailEl) emailEl.classList.add("input-error");
          if (window.Toast) window.Toast.show("Please enter a valid email address.");
          if (emailEl) emailEl.focus();
          return;
        }

        const submitBtn = form.querySelector("button[type='submit']");
        if (submitBtn) submitBtn.disabled = true;

        try {
          const res = await window.AuthAPI.login({ email: email, password: pwd });

          if (!res || !res.success) {
            const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
            const rawErr = res ? (res.error !== undefined && res.error !== null ? res.error : res.message) : null;
            const errMsg = String(normalizeFn ? normalizeFn(rawErr, "Invalid email address or password.") : "Invalid email address or password.");
            const lowerMsg = errMsg.toLowerCase();
            const isUnverified = res.status === 401 && (
              lowerMsg.includes("verify") ||
              lowerMsg.includes("confirm") ||
              lowerMsg.includes("unconfirmed") ||
              (res.data && res.data.code === "EMAIL_NOT_VERIFIED")
            );

            if (isUnverified) {
              if (emailEl) emailEl.classList.add("input-error");
              const showMsg = "Please verify your email before logging in.";
              if (window.Toast) window.Toast.show(showMsg);
              showResendVerificationUI(form, email, showMsg);
            } else {
              if (emailEl) emailEl.classList.add("input-error");
              if (pwdEl) pwdEl.classList.add("input-error");
              const noticeContainer = form.querySelector(".unverified-notice-container");
              if (noticeContainer) noticeContainer.remove();
              if (window.Toast) window.Toast.show(errMsg);
            }
            return;
          }

          const noticeContainer = form.querySelector(".unverified-notice-container");
          if (noticeContainer) noticeContainer.remove();

          const user = (res.data && res.data.user) ? res.data.user : {};

          function recordCustomerLogin(u) {
            const LOGINS_KEY = "rv_customer_logins";
            let logins = window.StorageUtils ? window.StorageUtils.readJSON(LOGINS_KEY, []) : [];
            const now = new Date();
            const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
            const dayName = days[now.getDay()];
            const newEntry = {
              id: "log_" + now.getTime() + "_" + Math.floor(Math.random() * 1000),
              userName: u.name || "Customer",
              userEmail: u.email || email,
              timestamp: now.toISOString(),
              dateStr: now.toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
              dayOfWeek: dayName
            };
            logins.unshift(newEntry);
            logins = logins.slice(0, 100);
            if (window.StorageUtils) {
              window.StorageUtils.writeJSON(LOGINS_KEY, logins);
            }
          }

          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(CURRENT_USER_KEY, user);
            window.StorageUtils.writeJSON(CONFIG_USER_KEY, user);
          }
          recordCustomerLogin(user);

          // Synchronize account cart & process any pending Add to Bag item
          const userCartKey = "rv_cart_" + user.email;
          let userCart = window.StorageUtils ? window.StorageUtils.readJSON(userCartKey, null) : null;
          if (!userCart) {
            userCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];
          }

          const pending = window.StorageUtils ? window.StorageUtils.readJSON("rv_pending_add_to_bag", null) : null;
          if (pending && pending.item) {
            const item = pending.item;
            const existing = userCart.find(function(i) { return i.id === item.id && (i.size || 'M') === (item.size || 'M'); });
            if (existing) {
              existing.qty += (item.qty || 1);
            } else {
              userCart.push(item);
            }
            if (window.StorageUtils) {
              window.StorageUtils.remove("rv_pending_add_to_bag");
            }
          }

          if (window.StorageUtils) {
            window.StorageUtils.writeJSON("rv_cart", userCart);
            window.StorageUtils.writeJSON(userCartKey, userCart);
          }

          if (window.NavbarComponent) {
            if (window.NavbarComponent.updateUserAvatar) window.NavbarComponent.updateUserAvatar(user);
            const count = userCart.reduce(function(sum, i) { return sum + (i.qty || 1); }, 0);
            if (window.NavbarComponent.updateCartBadge) window.NavbarComponent.updateCartBadge(count);
          }

          if (window.Toast) {
            if (pending && pending.item) {
              window.Toast.show(`Welcome back, ${user.name || 'Customer'}! ${pending.item.name || 'Item'} added to your bag.`);
            } else {
              window.Toast.show(`Welcome back, ${user.name || 'Customer'}!`);
            }
          }

          const openModal = document.querySelector(".login-overlay.open, .modal-overlay.open");
          if (openModal && window.Modal) {
            window.Modal.closeAll();
          } else {
            setTimeout(function() {
              if (pending && pending.returnUrl && !pending.returnUrl.includes("login.html")) {
                window.location.href = pending.returnUrl;
              } else if (window.location.pathname.includes("/pages/auth/") || window.location.pathname.includes("/pages/customer/") || window.location.pathname.includes("/pages/profile/")) {
                window.location.href = "../../index.html";
              } else {
                window.location.reload();
              }
            }, 500);
          }
        } catch (err) {
          const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
          const errMsg = String(normalizeFn ? normalizeFn(err, "Login error occurred. Please try again.") : "Login error occurred. Please try again.");
          if (window.Toast) window.Toast.show(errMsg);
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    initEyeToggles();
    initForms();
    checkUrlParams();
  });
})();

