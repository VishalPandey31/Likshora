/* =========================================================
   LIKSHORA — Modal Component System
   Reusable modal manager for dialogs, auth, checkout & about
   ========================================================= */

window.Modal = (function() {
  function switchAuthTab(tabName) {
    const tabLogin = document.getElementById("tabLogin");
    const tabSignup = document.getElementById("tabSignup");
    const formOtp = document.getElementById("loginFormOtp");
    const formEmail = document.getElementById("loginFormEmail") || document.getElementById("loginForm");
    const formSignup = document.getElementById("signupForm");

    if (tabName === "signup") {
      if (tabSignup) tabSignup.classList.add("active");
      if (tabLogin) tabLogin.classList.remove("active");
      if (formSignup) formSignup.classList.remove("hidden");
      if (formOtp) formOtp.classList.add("hidden");
      if (formEmail) formEmail.classList.add("hidden");
    } else if (tabName === "login") {
      if (tabLogin) tabLogin.classList.add("active");
      if (tabSignup) tabSignup.classList.remove("active");
      if (formSignup) formSignup.classList.add("hidden");
      if (formEmail) formEmail.classList.remove("hidden");
      if (formOtp) formOtp.classList.add("hidden");
    }
  }

  function initListeners() {
    document.addEventListener("keydown", function(e) {
      if (e.key === "Escape") {
        const openModals = document.querySelectorAll(".modal-overlay.open, .login-overlay.open");
        openModals.forEach(function(modal) {
          modal.classList.remove("open");
        });
      }
    });

    document.addEventListener("click", function(e) {
      if (e.target.classList.contains("modal-overlay") || e.target.classList.contains("login-overlay")) {
        e.target.classList.remove("open");
      }

      // Handle data-tab tab switching clicks
      const tabBtn = e.target.closest("[data-tab]");
      if (tabBtn) {
        const tab = tabBtn.dataset.tab;
        if (tab) {
          e.preventDefault();
          switchAuthTab(tab);
          const accountOverlay = document.getElementById("accountOverlay");
          if (accountOverlay) accountOverlay.classList.add("open");
        }
      }

      // Handle Auth Gate Modal actions
      const gateSignup = e.target.closest("#authGateSignup");
      if (gateSignup) {
        const gateOverlay = document.getElementById("authGateOverlay");
        if (gateOverlay) gateOverlay.classList.remove("open");
        switchAuthTab("signup");
        const accountOverlay = document.getElementById("accountOverlay");
        if (accountOverlay) accountOverlay.classList.add("open");
      }

      const gateLogin = e.target.closest("#authGateLogin");
      if (gateLogin) {
        const gateOverlay = document.getElementById("authGateOverlay");
        if (gateOverlay) gateOverlay.classList.remove("open");
        switchAuthTab("login");
        const accountOverlay = document.getElementById("accountOverlay");
        if (accountOverlay) accountOverlay.classList.add("open");
      }

      // Handle Email vs OTP login switching buttons inside modal
      const useEmail = e.target.closest("#useEmailBtn");
      if (useEmail) {
        const formOtp = document.getElementById("loginFormOtp");
        const formEmail = document.getElementById("loginFormEmail") || document.getElementById("loginForm");
        if (formOtp) formOtp.classList.add("hidden");
        if (formEmail) formEmail.classList.remove("hidden");
      }

      const usePhone = e.target.closest("#usePhoneBtn");
      if (usePhone) {
        const formOtp = document.getElementById("loginFormOtp");
        const formEmail = document.getElementById("loginFormEmail") || document.getElementById("loginForm");
        if (formEmail) formEmail.classList.add("hidden");
        if (formOtp) formOtp.classList.remove("hidden");
      }

      // Handle Size Guide triggers globally across all pages
      const sizeGuideTrigger = e.target.closest(".size-guide-link, #pdpSizeGuideBtn, a[href*='size-guide']");
      if (sizeGuideTrigger) {
        e.preventDefault();
        const modal = ensureSizeGuideModal();
        modal.classList.add("open");
      } else if (e.target.tagName === "A" && (e.target.textContent || "").trim().toLowerCase().includes("size guide")) {
        e.preventDefault();
        const modal = ensureSizeGuideModal();
        modal.classList.add("open");
      }
    });
  }

  function getSizeGuideImagePath() {
    const isSubpage = window.location.pathname.includes("/pages/");
    return isSubpage ? "../../assets/images/website/size-guide.jpg" : "assets/images/website/size-guide.jpg";
  }

  function ensureSizeGuideModal() {
    let overlay = document.getElementById("sizeGuideOverlay");
    const imgSrc = getSizeGuideImagePath();

    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.id = "sizeGuideOverlay";
      overlay.innerHTML = `
        <div class="modal modal-size-guide" style="max-width: 680px; width: 92vw; padding: 1.5em 1.2em; text-align: center; max-height: 90vh; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
          <button class="icon-btn modal-close" id="sizeGuideClose" aria-label="Close Size Guide" style="position: absolute; top: 1em; right: 1em; z-index: 10;">&times;</button>
          <h3 style="font-family: var(--font-display); font-size: 1.3rem; margin-top: 0; margin-bottom: 0.8em; color: var(--ink);">Likshora Size Guide</h3>
          <div class="size-guide-img-wrap" style="max-height: 75vh; overflow-y: auto; width: 100%; text-align: center; -webkit-overflow-scrolling: touch;">
            <img id="sizeGuideImg" src="${imgSrc}" alt="Likshora Size Guide — All measurements in inches" style="max-width: 100%; height: auto; object-fit: contain; border-radius: var(--radius-sm); display: block; margin: 0 auto;">
          </div>
        </div>
      `;
      document.body.appendChild(overlay);

      const closeBtn = overlay.querySelector("#sizeGuideClose");
      if (closeBtn) {
        closeBtn.addEventListener("click", function() {
          overlay.classList.remove("open");
        });
      }

      overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
          overlay.classList.remove("open");
        }
      });
    } else {
      const img = overlay.querySelector("#sizeGuideImg");
      if (img) img.src = imgSrc;
    }

    return overlay;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initListeners);
  } else {
    initListeners();
  }

  return {
    open: function(overlayId) {
      if (overlayId === "sizeGuideOverlay") {
        const modal = ensureSizeGuideModal();
        modal.classList.add("open");
        return;
      }
      const overlay = document.getElementById(overlayId);
      if (overlay) {
        overlay.classList.add("open");
      }
    },
    close: function(overlayId) {
      const overlay = document.getElementById(overlayId);
      if (overlay) {
        overlay.classList.remove("open");
      }
    },
    closeAll: function() {
      const openModals = document.querySelectorAll(".modal-overlay.open, .login-overlay.open");
      openModals.forEach(function(modal) {
        modal.classList.remove("open");
      });
    },
    switchAuthTab: switchAuthTab,
    openSizeGuide: function() {
      const modal = ensureSizeGuideModal();
      modal.classList.add("open");
    }
  };
})();
