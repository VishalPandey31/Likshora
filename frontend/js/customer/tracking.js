/* =========================================================
   LIKSHORA — Order Tracking & Contact Form Controller
   Dynamic 6-stage tracking timeline simulation & contact form validation
   ========================================================= */

(function() {
  const ORDERS_KEY = "rv_orders";
  const LAST_ORDER_KEY = "rv_last_order";

  const MOCK_FALLBACK_ORDER = null;

  function getOrderNumberFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("order") || "";
  }

  function lookupOrder(queryNum) {
    if (!queryNum) {
      const lastOrder = window.StorageUtils ? window.StorageUtils.readJSON(LAST_ORDER_KEY, null) : null;
      if (lastOrder) return lastOrder;
      return null;
    }

    const orders = window.StorageUtils ? window.StorageUtils.readJSON(ORDERS_KEY, []) : [];
    const match = orders.find(function(o) { return o.orderNumber.toUpperCase() === queryNum.toUpperCase(); });
    if (match) return match;

    

    return null;
  }

  function renderTrackingTimeline(stageIndex) {
    const stages = [
      { key: 1, label: "Processing", sub: "Order Received" },
      { key: 2, label: "Confirmed", sub: "Payment Verified" },
      { key: 3, label: "Packed", sub: "Quality Checked" },
      { key: 4, label: "Shipped", sub: "In Transit" },
      { key: 5, label: "Out for Delivery", sub: "With Courier" },
      { key: 6, label: "Delivered", sub: "Handed Over" }
    ];

    const currentStage = stageIndex || 4; // Default to Shipped for demo

    return stages.map(function(s) {
      let stateClass = "";
      if (s.key < currentStage) stateClass = "completed";
      else if (s.key === currentStage) stateClass = "current";

      const iconContent = s.key < currentStage ? "✓" : s.key;

      return `
        <div class="timeline-step ${stateClass}">
          <div class="timeline-icon">${iconContent}</div>
          <span class="timeline-label">${s.label}</span>
          <span class="timeline-time">${s.sub}</span>
        </div>
      `;
    }).join("");
  }

  function renderTrackingCard(order) {
    const cardEl = document.getElementById("trackingCard");
    const notFoundEl = document.getElementById("trackingNotFound");

    if (!cardEl || !notFoundEl) return;

    if (!order) {
      cardEl.classList.add("hidden");
      notFoundEl.classList.remove("hidden");
      return;
    }

    cardEl.classList.remove("hidden");
    notFoundEl.classList.add("hidden");

    const orderNumEl = document.getElementById("trackingOrderNum");
    const orderDateEl = document.getElementById("trackingOrderDate");
    const orderTotalEl = document.getElementById("trackingOrderTotal");
    const orderStatusBadge = document.getElementById("trackingStatusBadge");
    const timelineWrap = document.getElementById("trackingTimelineWrap");
    const addressEl = document.getElementById("trackingAddress");
    const carrierEl = document.getElementById("trackingCarrier");
    const itemsBody = document.getElementById("trackingItemsBody");

    if (orderNumEl) orderNumEl.textContent = "Order #" + order.orderNumber;
    if (orderDateEl) orderDateEl.textContent = "Placed on " + (order.date || "Today");
    if (orderTotalEl) orderTotalEl.textContent = window.Formatters.formatINR(order.grandTotal || 2299);
    if (orderStatusBadge) orderStatusBadge.textContent = order.status || "Shipped & In Transit";

    if (timelineWrap) {
      timelineWrap.innerHTML = renderTrackingTimeline(order.stage || 4);
    }

    if (addressEl && order.address) {
      const a = order.address;
      addressEl.innerHTML = `<strong>${window.Formatters.escapeHTML(a.recipient || 'Customer')}</strong><br>${window.Formatters.escapeHTML(a.street)}, ${window.Formatters.escapeHTML(a.city)}, ${window.Formatters.escapeHTML(a.state)} - ${window.Formatters.escapeHTML(a.pincode)}`;
    }

    if (carrierEl) {
      carrierEl.textContent = order.carrier || "Bluedart Priority Express (AWB: 89432019)";
    }

    if (itemsBody && order.items) {
      itemsBody.innerHTML = order.items.map(function(item) {
        return `
          <tr>
            <td style="font-weight:600;">${window.Formatters.escapeHTML(item.name)} (x${item.qty})</td>
            <td style="text-align:right; font-weight:600;">${window.Formatters.formatINR(item.price * item.qty)}</td>
          </tr>
        `;
      }).join("");
    }
  }

  function initContactForm() {
    const contactForm = document.getElementById("contactForm");
    if (!contactForm) return;

    contactForm.addEventListener("submit", function(e) {
      e.preventDefault();

      const name = document.getElementById("contactFormName").value.trim();
      const email = document.getElementById("contactFormEmail").value.trim();
      const subject = document.getElementById("contactFormSubject").value;
      const message = document.getElementById("contactFormMessage").value.trim();

      if (!name || !email || !message) {
        if (window.Toast) window.Toast.show("Please fill out all required fields.");
        return;
      }

      if (window.Validation && !window.Validation.isValidEmail(email)) {
        if (window.Toast) window.Toast.show("Please enter a valid email address.");
        return;
      }

      // Success feedback without sending to backend
      contactForm.reset();
      if (window.Toast) window.Toast.show("Thank you! Your message has been sent. We'll reply within 24 hours.");
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    const queryNum = getOrderNumberFromURL();
    const trackingInput = document.getElementById("trackingInput");
    if (trackingInput && queryNum) trackingInput.value = queryNum;

    const initialOrder = lookupOrder(queryNum);
    renderTrackingCard(initialOrder);

    const trackBtn = document.getElementById("trackingBtn");
    if (trackBtn && trackingInput) {
      trackBtn.addEventListener("click", function() {
        const num = trackingInput.value.trim();
        const order = lookupOrder(num);
        renderTrackingCard(order);
      });
    }

    initContactForm();

    // Modals
    document.getElementById("navAboutBtn").addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    const navAboutBtnFooter = document.getElementById("navAboutBtnFooter");
    if (navAboutBtnFooter) navAboutBtnFooter.addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    document.getElementById("aboutClose").addEventListener("click", function() { window.Modal.close("aboutOverlay"); });

    document.getElementById("accountToggle").addEventListener("click", function() { window.Modal.open("accountOverlay"); });
    document.getElementById("accountClose").addEventListener("click", function() { window.Modal.close("accountOverlay"); });
    document.getElementById("cartToggle").addEventListener("click", function() { window.Modal.open("cartDrawer"); document.getElementById("drawerOverlay").classList.add("open"); });
    document.getElementById("cartClose").addEventListener("click", function() { window.Modal.close("cartDrawer"); document.getElementById("drawerOverlay").classList.remove("open"); });
    document.getElementById("drawerOverlay").addEventListener("click", function() { window.Modal.close("cartDrawer"); document.getElementById("drawerOverlay").classList.remove("open"); });
  });
})();
