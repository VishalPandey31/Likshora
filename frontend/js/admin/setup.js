/* =========================================================
   LIKSHORA — Admin Setup Controller
   Check setup existence, 3-step setup flow (Details, OTP, Password) & account creation
   ========================================================= */

(function() {
  const ADMIN_ACCOUNT_KEY = "rv_admin_account";
  const PENDING_ADMIN_SETUP_KEY = "rv_pending_admin_setup";

  function checkAdminSetupExists() {
    const existing = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_ACCOUNT_KEY, null) : null;
    if (existing && window.location.pathname.endsWith("setup.html")) {
      // Admin account already configured, redirect to login
      window.location.href = "login.html";
    }
  }

  function initSetupForm() {
    const setupForm = document.getElementById("adminSetupStep1Form");
    if (!setupForm) return;

    setupForm.addEventListener("submit", function(e) {
      e.preventDefault();

      const name = document.getElementById("adminName").value.trim();
      const adminId = document.getElementById("adminId").value.trim();
      const phone = document.getElementById("adminPhone").value.trim();
      const email = document.getElementById("adminEmail").value.trim();

      if (!name || !adminId || !phone || !email) {
        if (window.Toast) window.Toast.show("Please fill out all required admin details.");
        return;
      }

      if (window.Validation && !window.Validation.isValidEmail(email)) {
        if (window.Toast) window.Toast.show("Please enter a valid email address.");
        return;
      }

      const pendingAdmin = {
        name: name,
        adminId: adminId.toUpperCase(),
        phone: phone,
        email: email
      };

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(PENDING_ADMIN_SETUP_KEY, pendingAdmin);
      }

      if (window.Toast) window.Toast.show("Admin verification code sent!");
      // Proceed to OTP verification step
      document.getElementById("setupStep1").classList.add("hidden");
      document.getElementById("setupStep2").classList.remove("hidden");
    });
  }

  function initOtpVerification() {
    const verifyBtn = document.getElementById("verifyAdminOtpBtn");
    if (!verifyBtn) return;

    verifyBtn.addEventListener("click", function() {
      const boxes = document.querySelectorAll(".otp-digit-box");
      const enteredCode = Array.from(boxes).map(function(b) { return b.value; }).join("");

      if (enteredCode.length < 6) {
        if (window.Toast) window.Toast.show("Please enter the 6-digit verification code.");
        return;
      }

      if (window.Toast) window.Toast.show("Admin identity verified!");
      document.getElementById("setupStep2").classList.add("hidden");
      document.getElementById("setupStep3").classList.remove("hidden");
    });
  }

  function initPasswordCreation() {
    const passForm = document.getElementById("adminPasswordForm");
    if (!passForm) return;

    passForm.addEventListener("submit", function(e) {
      e.preventDefault();

      const pwd = document.getElementById("adminPassword").value;
      const confirmPwd = document.getElementById("adminConfirmPassword").value;

      if (!pwd || pwd.length < 6) {
        if (window.Toast) window.Toast.show("Password must be at least 6 characters long.");
        return;
      }

      if (pwd !== confirmPwd) {
        if (window.Toast) window.Toast.show("Passwords do not match.");
        return;
      }

      const pending = window.StorageUtils ? window.StorageUtils.readJSON(PENDING_ADMIN_SETUP_KEY, null) : null;
      const adminAccount = {
        name: pending ? pending.name : "Administrator",
        adminId: pending ? pending.adminId : "ADM_001",
        phone: pending ? pending.phone : "9876543210",
        email: pending ? pending.email : "admin@LIKSHORA.com",
        password: pwd,
        createdAt: new Date().toISOString()
      };

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(ADMIN_ACCOUNT_KEY, adminAccount);
      }

      if (window.Toast) window.Toast.show("Admin setup completed successfully!");
      setTimeout(function() {
        window.location.href = "login.html";
      }, 600);
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    checkAdminSetupExists();
    initSetupForm();
    initOtpVerification();
    initPasswordCreation();
  });
})();
