/* =========================================================
   LIKSHORA — Admin Orders & Fulfillment Controller
   Order table, search, filter, pagination & order detail status updates
   ========================================================= */

(function() {
  const ORDERS_KEY = "rv_orders";

  const DEFAULT_ORDERS = [];

  let orders = window.StorageUtils ? window.StorageUtils.readJSON(ORDERS_KEY, DEFAULT_ORDERS) : DEFAULT_ORDERS;
  let currentPage = 1;
  const itemsPerPage = 6;

  function saveOrders() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(ORDERS_KEY, orders);
    }
  }

  function getOrderIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
  }

  async function renderOrdersTable() {
    const tableBody = document.getElementById("adminOrdersTableBody");
    const countEl = document.getElementById("adminOrdersCount");
    if (!tableBody) return;

    const query = document.getElementById("adminOrderSearch") ? document.getElementById("adminOrderSearch").value.trim().toLowerCase() : "";
    const statusFilter = document.getElementById("adminOrderStatusFilter") ? document.getElementById("adminOrderStatusFilter").value : "all";

    let fetchedOrders = orders;
    if (window.AdminAPI && window.AdminAPI.getAdminOrders) {
      try {
        const res = await window.AdminAPI.getAdminOrders();
        if (res.success && res.data) {
          fetchedOrders = Array.isArray(res.data) ? res.data : (res.data.orders || []);
        }
      } catch (err) {
        console.warn("Could not fetch admin orders from API:", err);
      }
    }

    let filtered = fetchedOrders.filter(function(o) {
      const orderNum = o.order_number || o.orderNumber || String(o.id);
      const custName = (o.user ? o.user.name : (o.contact ? o.contact.name : "Customer"));
      const matchQ = !query || orderNum.toLowerCase().includes(query) || custName.toLowerCase().includes(query);
      const matchS = statusFilter === "all" || o.order_status === statusFilter || o.status === statusFilter;
      return matchQ && matchS;
    });

    if (countEl) countEl.textContent = `Showing ${filtered.length} orders`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No orders match the selected search or filter.</td></tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(function(o) {
      const orderNum = o.order_number || o.orderNumber || String(o.id);
      const orderId = o.id || orderNum;
      const custName = o.user ? o.user.name : (o.contact ? o.contact.name : "Customer");
      const custEmail = o.user ? o.user.email : (o.contact ? o.contact.email : "");
      const totalAmount = o.total_amount !== undefined ? o.total_amount : o.grandTotal;
      const orderStatus = o.order_status || o.status || "Processing";
      const paymentStatus = o.payment_status || "Paid";

      let statusPillClass = "pending";
      if (orderStatus === "Delivered" || orderStatus === "delivered") statusPillClass = "success";
      if (orderStatus === "Processing" || orderStatus === "confirmed") statusPillClass = "alert";

      return `
        <tr data-id="${orderNum}">
          <td><strong style="font-size:.9rem;">${window.Formatters.escapeHTML(orderNum)}</strong></td>
          <td>
            <div>
              <strong style="font-size:.88rem;">${window.Formatters.escapeHTML(custName)}</strong>
              <p style="margin:0; font-size:.74rem; color:var(--admin-ink-soft);">${window.Formatters.escapeHTML(custEmail)}</p>
            </div>
          </td>
          <td style="color:var(--admin-ink-soft); font-size:.82rem;">${o.created_at ? new Date(o.created_at).toLocaleDateString("en-IN") : (o.date || 'Today')}</td>
          <td style="font-weight:600;">${window.Formatters.formatINR(totalAmount)}</td>
          <td><span class="status-pill success">${window.Formatters.escapeHTML(paymentStatus)}</span></td>
          <td><span class="status-pill ${statusPillClass}">${window.Formatters.escapeHTML(orderStatus)}</span></td>
          <td style="text-align:right;">
            <a href="order-details.html?id=${orderId}" class="btn-admin-secondary" style="padding:.3em .7em; font-size:.78rem; text-decoration:none;">View Details &rarr;</a>
          </td>
        </tr>
      `;
    }).join("");
  }

  async function renderOrderDetailsPage() {
    const orderId = getOrderIdFromURL();
    if (!orderId) return;

    let order = null;
    if (window.OrderAPI && window.OrderAPI.getOrderById) {
      try {
        const res = await window.OrderAPI.getOrderById(orderId);
        if (res.success && res.data) {
          order = res.data.order || res.data;
        }
      } catch (err) {
        console.warn("Could not fetch order detail from API:", err);
      }
    }

    if (!order) {
      order = orders.find(function(o) { return String(o.orderNumber) === String(orderId) || String(o.id) === String(orderId); });
    }

    if (!order) return;

    const orderNum = order.order_number || order.orderNumber || String(order.id);
    const numericId = order.id;

    const titleEl = document.getElementById("adminOrderDetailTitle");
    const dateEl = document.getElementById("adminOrderDetailDate");
    const statusSelect = document.getElementById("adminOrderStatusSelect");
    const carrierInput = document.getElementById("adminOrderCarrierInput");
    const customerBox = document.getElementById("adminOrderCustomerBox");
    const addressBox = document.getElementById("adminOrderAddressBox");
    const itemsBody = document.getElementById("adminOrderItemsBody");
    const subtotalEl = document.getElementById("adminOrderSubtotal");
    const shippingEl = document.getElementById("adminOrderShipping");
    const totalEl = document.getElementById("adminOrderGrandTotal");

    if (titleEl) titleEl.textContent = "Order #" + orderNum;
    if (dateEl) dateEl.textContent = "Placed on " + (order.created_at ? new Date(order.created_at).toLocaleDateString("en-IN") : (order.date || "Today"));
    if (statusSelect) statusSelect.value = order.order_status || order.status || "Processing";
    if (carrierInput) carrierInput.value = order.carrier || (order.shipment ? order.shipment.courier_name : "");

    const custName = order.user ? order.user.name : (order.contact ? order.contact.name : "Customer");
    const custEmail = order.user ? order.user.email : (order.contact ? order.contact.email : "");
    const custPhone = order.user ? order.user.phone : (order.contact ? order.contact.phone : "9876543210");

    if (customerBox) {
      customerBox.innerHTML = `
        <strong>Name:</strong> ${window.Formatters.escapeHTML(custName)}<br>
        <strong>Email:</strong> ${window.Formatters.escapeHTML(custEmail)}<br>
        <strong>Phone:</strong> +91 ${window.Formatters.escapeHTML(custPhone)}
      `;
    }

    if (addressBox) {
      const a = order.shipping_address_rel || order.address;
      if (a) {
        addressBox.innerHTML = `
          <strong>Recipient:</strong> ${window.Formatters.escapeHTML(a.recipient || a.name || custName)}<br>
          ${window.Formatters.escapeHTML(a.street || a.address_line1 || '')}, ${window.Formatters.escapeHTML(a.city)}, ${window.Formatters.escapeHTML(a.state)} - ${window.Formatters.escapeHTML(a.pincode)}
        `;
      }
    }

    const orderItemsList = order.items || order.order_items || [];
    if (itemsBody) {
      itemsBody.innerHTML = orderItemsList.map(function(item) {
        const prodName = item.product ? item.product.name : (item.name || "Product");
        const price = item.price !== undefined ? item.price : (item.unit_price || 0);
        const qty = item.quantity || item.qty || 1;
        let rawImg = item.product ? item.product.image_url : item.image;
        let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;

        return `
          <tr>
            <td>
              <div style="display:flex; align-items:center; gap:1em;">
                <div style="width:40px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
                  ${imgPath ? '<img src="' + imgPath + '" style="width:100%; height:100%; object-fit:cover;">' : ''}
                </div>
                <strong>${window.Formatters.escapeHTML(prodName)} (${item.size || 'M'})</strong>
              </div>
            </td>
            <td>${window.Formatters.formatINR(price)}</td>
            <td>${qty}</td>
            <td style="text-align:right; font-weight:600;">${window.Formatters.formatINR(price * qty)}</td>
          </tr>
        `;
      }).join("");
    }

    const subtotalAmount = order.subtotal !== undefined ? order.subtotal : order.total_amount;
    const shippingFee = order.shipping_fee !== undefined ? order.shipping_fee : (order.shippingFee || 0);
    const grandTotalAmount = order.total_amount !== undefined ? order.total_amount : order.grandTotal;

    if (subtotalEl) subtotalEl.textContent = window.Formatters.formatINR(subtotalAmount);
    if (shippingEl) shippingEl.textContent = (shippingFee === 0) ? "FREE" : window.Formatters.formatINR(shippingFee);
    if (totalEl) totalEl.textContent = window.Formatters.formatINR(grandTotalAmount);

    // Save status update button & Shiprocket dispatch
    const updateBtn = document.getElementById("updateOrderStatusBtn");
    if (updateBtn) {
      updateBtn.addEventListener("click", async function() {
        const newStatus = statusSelect.value;
        if (window.AdminAPI && window.AdminAPI.updateOrderStatus) {
          const res = await window.AdminAPI.updateOrderStatus(numericId || orderId, newStatus);
          if (res.success) {
            if (window.Toast) window.Toast.show("Order status updated!");
            return;
          }
        }
        order.status = newStatus;
        saveOrders();
        if (window.Toast) window.Toast.show("Order status updated!");
      });
    }

    // Shiprocket Order Fulfillment Dispatch button
    const shiprocketBtn = document.getElementById("adminFulfillShiprocketBtn");
    if (shiprocketBtn) {
      shiprocketBtn.addEventListener("click", async function() {
        shiprocketBtn.disabled = true;
        shiprocketBtn.textContent = "Dispatching via Shiprocket...";
        if (window.AdminAPI && window.AdminAPI.fulfillShiprocketOrder) {
          const res = await window.AdminAPI.fulfillShiprocketOrder(numericId || orderId);
          if (res.success) {
            if (window.Toast) window.Toast.show("Shiprocket shipment created & AWB generated!");
            location.reload();
            return;
          } else {
            alert("Shiprocket dispatch error: " + (res.error || "Failed to create shipment"));
          }
        }
        shiprocketBtn.disabled = false;
        shiprocketBtn.textContent = "Dispatch Shiprocket Order";
      });
    }
  }

  function initAdminSidebarToggle() {
    const toggleBtn = document.getElementById("adminMenuToggle");
    const sidebar = document.getElementById("adminSidebar");
    const overlay = document.getElementById("adminSidebarOverlay");

    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        sidebar.classList.toggle("open");
        toggleBtn.classList.toggle("open");
        if (overlay) overlay.classList.toggle("open");
      });
    }

    if (overlay && sidebar) {
      overlay.addEventListener("click", function() {
        sidebar.classList.remove("open");
        if (toggleBtn) toggleBtn.classList.remove("open");
        overlay.classList.remove("open");
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    initAdminSidebarToggle();
    renderOrdersTable();
    renderOrderDetailsPage();

    const searchInput = document.getElementById("adminOrderSearch");
    const statusSelect = document.getElementById("adminOrderStatusFilter");

    if (searchInput) searchInput.addEventListener("input", window.Helpers ? window.Helpers.debounce(function() { currentPage = 1; renderOrdersTable(); }, 300) : function() { renderOrdersTable(); });
    if (statusSelect) statusSelect.addEventListener("change", function() { currentPage = 1; renderOrdersTable(); });
  });
})();
