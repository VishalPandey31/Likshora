/* =========================================================
   LIKSHORA — Admin Login & Session Controller
   Credential checking, protected route guard & session termination
   ========================================================= */

(function () {
  const ADMIN_ACCOUNT_KEY = "rv_admin_account";
  const ADMIN_SESSION_KEY = "rv_admin_session";

  const DEFAULT_FALLBACK_ADMIN = {
    name: "Admin Karan",
    adminId: "ADM_001",
    email: "karanrajput.officials@gmail.com",
    password: "Karan@2026"
  };

  function checkAdminSession() {
    const session = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_SESSION_KEY, null) : null;
    const path = window.location.pathname;

    // Secure all routes containing /admin, blocking unauthenticated access unconditionally
    if (path.includes("/admin") && !path.includes("login")) {
      if (!session) {
        // Enforce absolute path to avoid missing trailing-slash directory resolution issues
        window.location.href = "/admin/pages/login";
      }
    }
  }

  function initAdminLogin() {
    const loginForm = document.getElementById("adminLoginForm");
    if (!loginForm) return;

    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const identity = document.getElementById("adminIdentity").value.trim();
      const pwd = document.getElementById("adminPassword").value;

      if (!identity || !pwd) {
        if (window.Toast) window.Toast.show("Please enter both Admin ID/Email and password.");
        return;
      }

      const configuredAdmin = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_ACCOUNT_KEY, DEFAULT_FALLBACK_ADMIN) : DEFAULT_FALLBACK_ADMIN;

      const matchesIdentity = (identity.toUpperCase() === configuredAdmin.adminId.toUpperCase()) || (identity.toLowerCase() === configuredAdmin.email.toLowerCase());
      const matchesPassword = pwd === configuredAdmin.password;

      if (!matchesIdentity || !matchesPassword) {
        if (window.Toast) window.Toast.show("Invalid Admin ID, Email, or password.");
        return;
      }

      const adminSession = {
        adminId: configuredAdmin.adminId,
        name: configuredAdmin.name,
        email: configuredAdmin.email,
        loggedInAt: new Date().toISOString()
      };

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(ADMIN_SESSION_KEY, adminSession);
      }

      if (window.Toast) window.Toast.show(`Welcome to Admin Panel, ${configuredAdmin.name}`);
      setTimeout(function () {
        // Enforce absolute path to always hit the root dashboard regardless of caller depth
        window.location.href = "/admin/index.html";
      }, 500);
    });
  }

  function initAdminLogout() {
    document.querySelectorAll(".admin-logout-trigger").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        if (window.StorageUtils) {
          window.StorageUtils.writeJSON(ADMIN_SESSION_KEY, null);
        }
        if (window.Toast) window.Toast.show("Logged out of Admin Portal.");
        setTimeout(function () {
          // Absolute path prevents nested 404 cascades (e.g. /admin/pages/pages/login.html)
          window.location.href = "/admin/pages/login";
        }, 500);
      });
    });
  }

  function initAdminMobileNavigation() {
    const sidebar = document.querySelector(".admin-sidebar");
    if (!sidebar) return;

    let overlay = document.querySelector(".admin-sidebar-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "admin-sidebar-overlay";
      document.body.appendChild(overlay);
    }

    const headerLeft = document.querySelector(".admin-header-left");
    if (headerLeft && !headerLeft.querySelector(".admin-menu-toggle")) {
      const toggleBtn = document.createElement("button");
      toggleBtn.className = "admin-menu-toggle";
      toggleBtn.id = "adminMenuToggle";
      toggleBtn.setAttribute("aria-label", "Toggle Admin Navigation");
      toggleBtn.innerHTML = "<span></span><span></span><span></span>";
      headerLeft.insertBefore(toggleBtn, headerLeft.firstChild);

      toggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        const isOpen = sidebar.classList.toggle("open");
        overlay.classList.toggle("open", isOpen);
        toggleBtn.classList.toggle("open", isOpen);
      });

      overlay.addEventListener("click", function () {
        sidebar.classList.remove("open");
        overlay.classList.remove("open");
        toggleBtn.classList.remove("open");
      });

      sidebar.querySelectorAll(".admin-nav-menu a, .admin-logout-trigger").forEach(function (link) {
        link.addEventListener("click", function () {
          sidebar.classList.remove("open");
          overlay.classList.remove("open");
          toggleBtn.classList.remove("open");
        });
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    checkAdminSession();
    initAdminLogin();
    initAdminLogout();
    initAdminMobileNavigation();
  });
})();
