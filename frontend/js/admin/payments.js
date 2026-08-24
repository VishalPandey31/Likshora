/* =========================================================
   LIKSHORA — Admin Payments & Transactions Controller
   Mock payment gateway transaction log, status filters & metrics
   ========================================================= */

(function() {
  const PAYMENTS_KEY = "rv_payments";

  const DEFAULT_PAYMENTS = [];

  let payments = window.StorageUtils ? window.StorageUtils.readJSON(PAYMENTS_KEY, DEFAULT_PAYMENTS) : DEFAULT_PAYMENTS;
  let currentPage = 1;
  const itemsPerPage = 6;

  function renderPaymentsMetrics() {
    const totalRevEl = document.getElementById("payStatTotalRevenue");
    const totalTxnEl = document.getElementById("payStatTotalTxn");
    const totalRefundEl = document.getElementById("payStatTotalRefund");

    const totalCaptured = payments.filter(function(p) { return p.status === "Captured"; }).reduce(function(sum, p) { return sum + p.amount; }, 0);
    const totalRefunded = payments.filter(function(p) { return p.status === "Refunded"; }).reduce(function(sum, p) { return sum + p.amount; }, 0);

    if (totalRevEl) totalRevEl.textContent = window.Formatters.formatINR(totalCaptured);
    if (totalTxnEl) totalTxnEl.textContent = payments.length;
    if (totalRefundEl) totalRefundEl.textContent = window.Formatters.formatINR(totalRefunded);
  }

  function renderPaymentsTable() {
    const tableBody = document.getElementById("adminPaymentsTableBody");
    const countEl = document.getElementById("adminPaymentsCount");
    if (!tableBody) return;

    const query = document.getElementById("adminPaymentSearch") ? document.getElementById("adminPaymentSearch").value.trim().toLowerCase() : "";
    const methodFilter = document.getElementById("adminPaymentMethodFilter") ? document.getElementById("adminPaymentMethodFilter").value : "all";
    const statusFilter = document.getElementById("adminPaymentStatusFilter") ? document.getElementById("adminPaymentStatusFilter").value : "all";

    let filtered = payments.filter(function(p) {
      const matchQ = !query || p.txnId.toLowerCase().includes(query) || p.orderId.toLowerCase().includes(query) || p.customer.toLowerCase().includes(query);
      const matchM = methodFilter === "all" || p.method.toLowerCase().includes(methodFilter.toLowerCase());
      const matchS = statusFilter === "all" || p.status === statusFilter;
      return matchQ && matchM && matchS;
    });

    if (countEl) countEl.textContent = `Showing ${filtered.length} transactions`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No payment transactions match the selected criteria.</td></tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(function(p) {
      let statusClass = "success";
      if (p.status === "Pending") statusClass = "pending";
      if (p.status === "Refunded" || p.status === "Failed") statusClass = "alert";

      return `
        <tr>
          <td><code style="font-size:.82rem; font-weight:600;">${p.txnId}</code></td>
          <td style="font-weight:600;"><a href="order-details.html?id=${p.orderId}" style="color:var(--admin-gold); text-decoration:none;">${p.orderId}</a></td>
          <td>${window.Formatters.escapeHTML(p.customer)}</td>
          <td style="color:var(--admin-ink-soft); font-size:.82rem;">${p.date}</td>
          <td><span style="font-size:.82rem; background:var(--admin-bg); padding:.2em .6em; border-radius:4px; border:1px solid var(--admin-border);">${p.method}</span></td>
          <td style="font-weight:600;">${window.Formatters.formatINR(p.amount)}</td>
          <td><span class="status-pill ${statusClass}">${p.status}</span></td>
        </tr>
      `;
    }).join("");
  }

  document.addEventListener("DOMContentLoaded", function() {
    renderPaymentsMetrics();
    renderPaymentsTable();

    const searchInput = document.getElementById("adminPaymentSearch");
    const methodSelect = document.getElementById("adminPaymentMethodFilter");
    const statusSelect = document.getElementById("adminPaymentStatusFilter");

    if (searchInput) searchInput.addEventListener("input", window.Helpers ? window.Helpers.debounce(function() { currentPage = 1; renderPaymentsTable(); }, 300) : function() { renderPaymentsTable(); });
    if (methodSelect) methodSelect.addEventListener("change", function() { currentPage = 1; renderPaymentsTable(); });
    if (statusSelect) statusSelect.addEventListener("change", function() { currentPage = 1; renderPaymentsTable(); });
  });
})();
