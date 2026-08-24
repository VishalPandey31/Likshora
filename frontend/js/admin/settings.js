/* =========================================================
   LIKSHORA — Admin Portal Settings Controller
   Admin profile, password change, preferences & active sessions
   ========================================================= */

(function() {
  const ADMIN_ACCOUNT_KEY = "rv_admin_account";
  const ADMIN_SETTINGS_KEY = "rv_admin_settings";
  const ADMIN_SESSION_KEY = "rv_admin_session";

  const DEFAULT_ACCOUNT = {
    name: "System Administrator",
    adminId: "ADM_001",
    email: "admin@LIKSHORA.com",
    phone: "9876543210",
    password: "admin123"
  };

  const DEFAULT_SETTINGS = {
    currency: "INR (₹)",
    taxRate: 5,
    stockThreshold: 4,
    orderNotifications: true,
    lowStockNotifications: true
  };

  let account = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_ACCOUNT_KEY, DEFAULT_ACCOUNT) : DEFAULT_ACCOUNT;
  let settings = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_SETTINGS_KEY, DEFAULT_SETTINGS) : DEFAULT_SETTINGS;

  function populateSettingsFields() {
    const nameInput = document.getElementById("settingAdminName");
    const idInput = document.getElementById("settingAdminId");
    const emailInput = document.getElementById("settingAdminEmail");
    const phoneInput = document.getElementById("settingAdminPhone");
    const currencySelect = document.getElementById("settingCurrency");
    const taxInput = document.getElementById("settingTaxRate");
    const thresholdInput = document.getElementById("settingStockThreshold");
    const orderNotifToggle = document.getElementById("settingOrderNotif");
    const stockNotifToggle = document.getElementById("settingStockNotif");

    if (nameInput) nameInput.value = account.name || "";
    if (idInput) idInput.value = account.adminId || "";
    if (emailInput) emailInput.value = account.email || "";
    if (phoneInput) phoneInput.value = account.phone || "";
    if (currencySelect) currencySelect.value = settings.currency || "INR (₹)";
    if (taxInput) taxInput.value = settings.taxRate || 5;
    if (thresholdInput) thresholdInput.value = settings.stockThreshold || 4;
    if (orderNotifToggle) orderNotifToggle.checked = settings.orderNotifications !== false;
    if (stockNotifToggle) stockNotifToggle.checked = settings.lowStockNotifications !== false;
  }

  function initProfileForm() {
    const profileForm = document.getElementById("adminProfileSettingsForm");
    if (!profileForm) return;

    profileForm.addEventListener("submit", function(e) {
      e.preventDefault();

      account.name = document.getElementById("settingAdminName").value.trim();
      account.email = document.getElementById("settingAdminEmail").value.trim();
      account.phone = document.getElementById("settingAdminPhone").value.trim();

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(ADMIN_ACCOUNT_KEY, account);
      }

      if (window.Toast) window.Toast.show("Admin profile updated successfully!");
    });
  }

  function initPasswordForm() {
    const passwordForm = document.getElementById("adminPasswordSettingsForm");
    if (!passwordForm) return;

    passwordForm.addEventListener("submit", function(e) {
      e.preventDefault();

      const currentPwd = document.getElementById("settingCurrentPassword").value;
      const newPwd = document.getElementById("settingNewPassword").value;
      const confirmPwd = document.getElementById("settingConfirmPassword").value;

      if (currentPwd !== account.password) {
        if (window.Toast) window.Toast.show("Current password is incorrect.");
        return;
      }

      if (newPwd.length < 6) {
        if (window.Toast) window.Toast.show("New password must be at least 6 characters long.");
        return;
      }

      if (newPwd !== confirmPwd) {
        if (window.Toast) window.Toast.show("New passwords do not match.");
        return;
      }

      account.password = newPwd;
      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(ADMIN_ACCOUNT_KEY, account);
      }

      document.getElementById("settingCurrentPassword").value = "";
      document.getElementById("settingNewPassword").value = "";
      document.getElementById("settingConfirmPassword").value = "";

      if (window.Toast) window.Toast.show("Password changed successfully!");
    });
  }

  function initPreferencesForm() {
    const prefForm = document.getElementById("adminPreferencesForm");
    if (!prefForm) return;

    prefForm.addEventListener("submit", function(e) {
      e.preventDefault();

      settings.currency = document.getElementById("settingCurrency").value;
      settings.taxRate = parseFloat(document.getElementById("settingTaxRate").value);
      settings.stockThreshold = parseInt(document.getElementById("settingStockThreshold").value, 10);
      settings.orderNotifications = document.getElementById("settingOrderNotif").checked;
      settings.lowStockNotifications = document.getElementById("settingStockNotif").checked;

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(ADMIN_SETTINGS_KEY, settings);
      }

      if (window.Toast) window.Toast.show("Portal preferences saved!");
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    populateSettingsFields();
    initProfileForm();
    initPasswordForm();
    initPreferencesForm();
  });
})();
