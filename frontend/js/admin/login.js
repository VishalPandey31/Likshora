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

  async function checkAdminSession() {
    const session = window.StorageUtils ? window.StorageUtils.readJSON(ADMIN_SESSION_KEY, null) : null;
    const token = window.StorageUtils ? window.StorageUtils.readJSON("rv_access_token", null) : null;
    const path = window.location.pathname;

    // Secure all routes containing /admin, blocking unauthenticated access unconditionally
    if (path.includes("/admin") && !path.includes("login")) {
      if (!session || !token) {
        window.location.replace("/admin/pages/login");
        return;
      }

      try {
        const response = await fetch((window.RV_CONFIG.API_BASE_URL || "") + "/api/v1/auth/me", {
          headers: { "Authorization": "Bearer " + token }
        });

        if (!response.ok) {
          // Token invalid or expired, force logout
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(ADMIN_SESSION_KEY, null);
            window.StorageUtils.writeJSON("rv_access_token", null);
          }
          window.location.replace("/admin/pages/login");
        }
      } catch (err) {
        // Safe fallback for network error
        console.error("Auth Guard Error:", err);
      }
    } else if (path.includes("/admin/pages/login")) {
      // If user hits login page and IS authenticated, send to dashboard
      if (session && token) {
        try {
          const response = await fetch((window.RV_CONFIG.API_BASE_URL || "") + "/api/v1/auth/me", {
            headers: { "Authorization": "Bearer " + token }
          });
          if (response.ok) {
            window.location.replace("/admin/pages/dashboard.html");
          }
        } catch (e) { }
      }
    }
  }

  function initAdminLogin() {
    const loginForm = document.getElementById("adminLoginForm");
    if (!loginForm) return;

    loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const identity = document.getElementById("adminIdentity").value.trim();
      const pwd = document.getElementById("adminPassword").value;

      if (!identity || !pwd) {
        if (window.Toast) window.Toast.show("Please enter both Admin ID/Email and password.");
        return;
      }

      try {
        const response = await fetch((window.RV_CONFIG.API_BASE_URL || "") + "/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: identity, password: pwd })
        });

        const resData = await response.json();

        if (!response.ok || !resData.success) {
          if (window.Toast) window.Toast.show(resData.message || "Invalid Admin ID, Email, or password.");
          return;
        }

        const user = resData.data.user;
        if (user.role !== "admin") {
          if (window.Toast) window.Toast.show("Access Denied: You do not have administrator permissions.");
          return;
        }

        const adminSession = {
          adminId: user.id,
          name: user.name,
          email: user.email,
          loggedInAt: new Date().toISOString()
        };

        if (window.StorageUtils) {
          window.StorageUtils.writeJSON(ADMIN_SESSION_KEY, adminSession);
          window.StorageUtils.writeJSON("rv_access_token", resData.data.access_token);
        }

        if (window.Toast) window.Toast.show(`Welcome to Admin Panel, ${user.name}`);
        setTimeout(function () {
          // Enforce absolute path to always hit the root dashboard regardless of caller depth
          window.location.href = "/admin/index.html";
        }, 500);
      } catch (err) {
        console.error("Login Error:", err);
        if (window.Toast) window.Toast.show("Network Error. Cannot connect to API.");
      }
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
