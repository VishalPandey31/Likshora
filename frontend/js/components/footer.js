/* =========================================================
   LIKSHORA — Footer Component Controller
   Footer links, dynamic year & reserved section placeholders
   ========================================================= */

window.FooterComponent = (function() {
  function updateYear() {
    const yearEl = document.getElementById("year");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  }

  function initShippingLink() {
    document.addEventListener("click", function(e) {
      const link = e.target.closest("a[href*='shipping-returns']");
      if (link) {
        const targetEl = document.getElementById("shipping-returns");
        if (targetEl) {
          e.preventDefault();
          targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    });
  }

  function initSizeGuideLink() {
    document.addEventListener("click", function(e) {
      const link = e.target.closest("a[href*='size-guide'], .size-guide-trigger, a");
      if (link && ((link.getAttribute("href") && link.getAttribute("href").includes("size-guide")) || (link.textContent || "").trim().toLowerCase() === "size guide")) {
        e.preventDefault();
        if (window.Modal && typeof window.Modal.openSizeGuide === "function") {
          window.Modal.openSizeGuide();
        }
      }
    });
  }

  function initPlaceholderLinks() {
    document.addEventListener("click", function(e) {
      const link = e.target.closest("a[href^='javascript:void']");
      if (link) {
        e.preventDefault();
      }
    });
  }

  return {
    init: function() {
      updateYear();
      initShippingLink();
      initSizeGuideLink();
      initPlaceholderLinks();
    }
  };
})();
