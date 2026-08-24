/* =========================================================
   LIKSHORA — Admin Shipping & Logistics Controller
   Shipment orders, courier assignment, AWB tracking & timeline
   ========================================================= */

(function() {
  const SHIPMENTS_KEY = "rv_shipments";

  const DEFAULT_SHIPMENTS = [
    {
      orderNumber: "ORD_K9X2A8",
      customer: "Ananya Sharma",
      courier: "Bluedart Priority Express",
      awb: "89432019",
      estDelivery: "15 Aug 2026",
      status: "Shipped",
      currentStep: 4,
      address: "Flat 402, Lotus Apartments, MG Road, Bengaluru - 560001",
      timeline: [
        { title: "Order Placed", date: "12 Aug 2026, 10:15 AM", completed: true },
        { title: "Payment Confirmed", date: "12 Aug 2026, 10:16 AM", completed: true },
        { title: "Packed & Sealed", date: "12 Aug 2026, 03:30 PM", completed: true },
        { title: "Shipped via Bluedart", date: "13 Aug 2026, 09:00 AM", completed: true },
        { title: "Out for Delivery", date: "Pending", completed: false },
        { title: "Delivered", date: "Pending", completed: false }
      ]
    },
    {
      orderNumber: "ORD_P4M901",
      customer: "Meera Kapoor",
      courier: "Delhivery Surface",
      awb: "DL7749102",
      estDelivery: "14 Aug 2026",
      status: "Delivered",
      currentStep: 6,
      address: "12 Heritage Lane, Indiranagar, Bengaluru - 560038",
      timeline: [
        { title: "Order Placed", date: "11 Aug 2026, 02:20 PM", completed: true },
        { title: "Payment Confirmed", date: "11 Aug 2026, 02:21 PM", completed: true },
        { title: "Packed & Sealed", date: "11 Aug 2026, 06:00 PM", completed: true },
        { title: "Shipped via Delhivery", date: "12 Aug 2026, 08:30 AM", completed: true },
        { title: "Out for Delivery", date: "12 Aug 2026, 11:00 AM", completed: true },
        { title: "Delivered", date: "12 Aug 2026, 04:15 PM", completed: true }
      ]
    },
    {
      orderNumber: "ORD_L88X12",
      customer: "Priya Nair",
      courier: "Shiprocket Partner Courier",
      awb: "Pending AWB",
      estDelivery: "18 Aug 2026",
      status: "Processing",
      currentStep: 1,
      address: "Suite 40, Tech Park, Whitefield, Bengaluru - 560066",
      timeline: [
        { title: "Order Placed", date: "12 Aug 2026, 11:45 AM", completed: true },
        { title: "Payment Confirmed", date: "12 Aug 2026, 11:46 AM", completed: true },
        { title: "Packed & Sealed", date: "Pending", completed: false },
        { title: "Shipped", date: "Pending", completed: false },
        { title: "Out for Delivery", date: "Pending", completed: false },
        { title: "Delivered", date: "Pending", completed: false }
      ]
    }
  ];

  let shipments = window.StorageUtils ? window.StorageUtils.readJSON(SHIPMENTS_KEY, DEFAULT_SHIPMENTS) : DEFAULT_SHIPMENTS;
  let editingShipmentId = null;

  function saveShipments() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(SHIPMENTS_KEY, shipments);
    }
  }

  function renderShipmentsTable() {
    const tableBody = document.getElementById("adminShippingTableBody");
    const countEl = document.getElementById("adminShippingCount");
    if (!tableBody) return;

    const query = document.getElementById("adminShippingSearch") ? document.getElementById("adminShippingSearch").value.trim().toLowerCase() : "";
    const statusFilter = document.getElementById("adminShippingStatusFilter") ? document.getElementById("adminShippingStatusFilter").value : "all";

    let filtered = shipments.filter(function(s) {
      const matchQ = !query || s.orderNumber.toLowerCase().includes(query) || s.customer.toLowerCase().includes(query) || s.awb.toLowerCase().includes(query);
      const matchS = statusFilter === "all" || s.status === statusFilter;
      return matchQ && matchS;
    });

    if (countEl) countEl.textContent = `Showing ${filtered.length} shipments`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No shipment orders match the search or filter.</td></tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(function(s) {
      let statusPillClass = "pending";
      if (s.status === "Delivered") statusPillClass = "success";
      if (s.status === "Processing") statusPillClass = "alert";

      return `
        <tr data-id="${s.orderNumber}">
          <td><strong style="font-size:.9rem;">${s.orderNumber}</strong></td>
          <td>${window.Formatters.escapeHTML(s.customer)}</td>
          <td>
            <div style="font-size:.86rem; font-weight:600;">${window.Formatters.escapeHTML(s.courier)}</div>
            <div style="font-size:.76rem; color:var(--admin-ink-soft);">AWB: ${window.Formatters.escapeHTML(s.awb)}</div>
          </td>
          <td style="font-size:.84rem;">${s.estDelivery}</td>
          <td style="max-width:220px; font-size:.8rem; color:var(--admin-ink-soft);">${window.Formatters.escapeHTML(s.address)}</td>
          <td><span class="status-pill ${statusPillClass}">${s.status}</span></td>
          <td style="text-align:right;">
            <div style="display:flex; gap:.4em; justify-content:flex-end;">
              <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-timeline="${s.orderNumber}">Timeline</button>
              <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-edit-shipment="${s.orderNumber}">Update AWB</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function initEditShipmentModal() {
    const saveBtn = document.getElementById("saveShipmentDetailsBtn");
    if (!saveBtn) return;

    saveBtn.addEventListener("click", function() {
      if (!editingShipmentId) return;

      const s = shipments.find(function(item) { return item.orderNumber === editingShipmentId; });
      if (s) {
        s.courier = document.getElementById("editCourierPartner").value.trim();
        s.awb = document.getElementById("editAwbNumber").value.trim();
        s.estDelivery = document.getElementById("editEstDelivery").value.trim();
        s.status = document.getElementById("editShipmentStatus").value;

        saveShipments();
        renderShipmentsTable();
        if (window.Modal) window.Modal.close("editShippingModal");
        if (window.Toast) window.Toast.show(`Shipment details updated for ${s.orderNumber}`);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    renderShipmentsTable();
    initEditShipmentModal();

    const searchInput = document.getElementById("adminShippingSearch");
    const statusSelect = document.getElementById("adminShippingStatusFilter");

    if (searchInput) searchInput.addEventListener("input", window.Helpers ? window.Helpers.debounce(function() { renderShipmentsTable(); }, 300) : function() { renderShipmentsTable(); });
    if (statusSelect) statusSelect.addEventListener("change", function() { renderShipmentsTable(); });

    const tableBody = document.getElementById("adminShippingTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", function(e) {
        const timelineBtn = e.target.closest("[data-timeline]");
        const editBtn = e.target.closest("[data-edit-shipment]");

        if (timelineBtn) {
          const id = timelineBtn.dataset.timeline;
          const s = shipments.find(function(item) { return item.orderNumber === id; });
          if (s && window.Modal) {
            const titleEl = document.getElementById("timelineModalTitle");
            const bodyEl = document.getElementById("timelineModalBody");
            if (titleEl) titleEl.textContent = `Shipment Timeline — ${s.orderNumber}`;
            if (bodyEl) {
              bodyEl.innerHTML = `
                <p style="font-size:.88rem; margin-bottom:1.5em;"><strong>Courier:</strong> ${s.courier} | <strong>AWB:</strong> ${s.awb}</p>
                <div style="display:flex; flex-direction:column; gap:1em;">
                  ${s.timeline.map(function(t, idx) {
                    const stepNum = idx + 1;
                    const isCompleted = t.completed;
                    const circleBg = isCompleted ? 'var(--admin-success)' : 'var(--admin-border)';
                    const textColor = isCompleted ? 'var(--admin-ink)' : 'var(--admin-ink-soft)';
                    return `
                      <div style="display:flex; items-center; gap:1em;">
                        <div style="width:28px; height:28px; border-radius:50%; background:${circleBg}; color:white; font-size:.8rem; font-weight:600; display:flex; align-items:center; justify-content:center; flex-shrink:0;">${stepNum}</div>
                        <div style="color:${textColor};">
                          <strong style="font-size:.9rem;">${t.title}</strong>
                          <p style="margin:0; font-size:.76rem;">${t.date}</p>
                        </div>
                      </div>
                    `;
                  }).join("")}
                </div>
              `;
            }
            window.Modal.open("shippingTimelineModal");
          }
        }

        if (editBtn) {
          editingShipmentId = editBtn.dataset.editShipment;
          const s = shipments.find(function(item) { return item.orderNumber === editingShipmentId; });
          if (s) {
            document.getElementById("editCourierPartner").value = s.courier;
            document.getElementById("editAwbNumber").value = s.awb;
            document.getElementById("editEstDelivery").value = s.estDelivery;
            document.getElementById("editShipmentStatus").value = s.status;
            if (window.Modal) window.Modal.open("editShippingModal");
          }
        }
      });
    }
  });
})();
