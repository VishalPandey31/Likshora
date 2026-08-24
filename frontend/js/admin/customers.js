/* =========================================================
   LIKSHORA — Admin Customers Controller
   Customer profiles, search, filter, order history, addresses, cart, wishlist, payments, search activity & account status
   ========================================================= */

(function() {
  function getCustomerIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
  }

  async function renderCustomersTable() {
    const tableBody = document.getElementById("adminCustomersTableBody");
    const countEl = document.getElementById("adminCustomerCount");
    if (!tableBody) return;

    const search = document.getElementById("adminCustomerSearch") ? document.getElementById("adminCustomerSearch").value.trim() : "";
    const statusFilter = document.getElementById("adminCustomerStatusFilter") ? document.getElementById("adminCustomerStatusFilter").value : "all";

    try {
      const res = await window.AdminAPI.getCustomers({ search: search });
      let customersList = [];
      if (res.success && res.data) {
        customersList = Array.isArray(res.data) ? res.data : (res.data.customers || []);
      }

      if (statusFilter !== "all") {
        customersList = customersList.filter(function(c) {
          const isActive = c.is_active !== false;
          if (statusFilter === "Active") return isActive;
          if (statusFilter === "Blocked") return !isActive;
          return true;
        });
      }

      if (countEl) countEl.textContent = `Showing ${customersList.length} customers`;

      if (customersList.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No customers match the search or filter.</td></tr>`;
        return;
      }

      tableBody.innerHTML = customersList.map(function(c) {
        const nameStr = c.name || "Customer";
        const initials = window.Formatters ? window.Formatters.getInitials(nameStr) : "CU";
        const isActive = c.is_active !== false;
        const isVerified = c.email_verified === true;
        const statusLabel = isActive ? "Active" : "Blocked";
        const statusPillClass = isActive ? "success" : "alert";
        const verifyLabel = isVerified ? "Verified" : "Not Verified";
        const verifyPillClass = isVerified ? "success" : "alert";
        const createdDate = c.created_at ? c.created_at.split('T')[0] : 'N/A';

        return `
          <tr data-id="${c.id}">
            <td>
              <div style="display:flex; align-items:center; gap:1em;">
                <div class="admin-chip-avatar" style="flex-shrink:0;">${initials}</div>
                <div>
                  <strong style="font-size:.9rem;">${window.Formatters.escapeHTML(nameStr)}</strong>
                  <p style="margin:0; font-size:.74rem; color:var(--admin-ink-soft);">ID: ${c.id}</p>
                </div>
              </div>
            </td>
            <td>${window.Formatters.escapeHTML(c.email || '')}</td>
            <td>${c.phone ? '+91 ' + window.Formatters.escapeHTML(c.phone) : 'N/A'}</td>
            <td><span class="status-pill ${verifyPillClass}">${verifyLabel}</span></td>
            <td><strong>${c.order_count || 0}</strong> orders</td>
            <td style="font-weight:600;">${window.Formatters.formatINR(c.total_spent || 0)}</td>
            <td><span class="status-pill ${statusPillClass}">${statusLabel}</span></td>
            <td style="font-size:.82rem; color:var(--admin-ink-soft);">${createdDate}</td>
            <td style="text-align:right;">
              <a href="customer-details.html?id=${c.id}" class="btn-admin-secondary" style="padding:.3em .7em; font-size:.78rem; text-decoration:none;">View Profile &rarr;</a>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      console.error("Failed to load admin customers list:", err);
      tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:2em; color:var(--admin-danger);">Failed to load customers from server.</td></tr>`;
    }
  }

  async function renderCustomerDetailsPage() {
    const custId = getCustomerIdFromURL();
    if (!custId) return;

    const titleEl = document.getElementById("adminCustomerDetailTitle");
    const subEl = document.getElementById("adminCustomerDetailSub");
    const avatarEl = document.getElementById("adminCustomerAvatar");
    const phoneEl = document.getElementById("adminCustomerPhone");
    const emailEl = document.getElementById("adminCustomerEmail");
    const statusPillEl = document.getElementById("adminCustomerStatusPill");
    const toggleStatusBtn = document.getElementById("toggleCustomerStatusBtn");
    const ordersBody = document.getElementById("adminCustomerOrdersTableBody");
    const addressBox = document.getElementById("adminCustomerAddressBox");
    const paymentsBody = document.getElementById("adminCustomerPaymentsTableBody");
    const cartBox = document.getElementById("adminCustomerCartBox");
    const wishlistBox = document.getElementById("adminCustomerWishlistBox");
    const searchBox = document.getElementById("adminCustomerSearchBox");
    const reviewsBox = document.getElementById("adminCustomerReviewsBox");
    const loginLogsBox = document.getElementById("adminCustomerLoginLogsBox");

    try {
      const res = await window.AdminAPI.getCustomerById(custId);
      if (!res.success || !res.data) {
        if (titleEl) titleEl.textContent = "Customer Not Found";
        return;
      }

      const cust = res.data;
      const isActive = cust.is_active !== false;

      if (titleEl) titleEl.textContent = cust.name || "Customer Profile";
      if (subEl) subEl.textContent = `Customer ID: ${cust.id} · Registered: ${cust.created_at ? cust.created_at.split('T')[0] : 'N/A'}`;
      if (avatarEl && window.Formatters) avatarEl.textContent = window.Formatters.getInitials(cust.name || "Customer");
      if (phoneEl) phoneEl.textContent = cust.phone ? "+91 " + cust.phone : "Not provided";
      if (emailEl) emailEl.textContent = cust.email || "N/A";

      if (statusPillEl) {
        statusPillEl.textContent = isActive ? "Active" : "Blocked";
        statusPillEl.className = `status-pill ${isActive ? 'success' : 'alert'}`;
      }

      if (toggleStatusBtn) {
        toggleStatusBtn.textContent = isActive ? "Block Customer Account" : "Unblock Account";
        toggleStatusBtn.className = isActive ? "btn-admin-danger" : "btn-admin-primary";

        toggleStatusBtn.onclick = async function() {
          try {
            const toggleRes = await window.AdminAPI.updateCustomerStatus(cust.id, !isActive);
            if (toggleRes.success) {
              if (window.Toast) window.Toast.show(toggleRes.message || "Account status updated");
              renderCustomerDetailsPage();
            } else {
              if (window.Toast) window.Toast.show(toggleRes.message || "Failed to update account status");
            }
          } catch (err) {
            console.error("Status update failure:", err);
          }
        };
      }

      // Render Addresses
      if (addressBox) {
        if (cust.addresses && cust.addresses.length > 0) {
          addressBox.innerHTML = cust.addresses.map(function(a) {
            return `
              <div style="margin-bottom:.8em; padding-bottom:.5em; border-bottom:1px solid var(--admin-border-light, #eee);">
                <strong style="color:var(--admin-gold);">${window.Formatters.escapeHTML(a.full_name || 'Address')}:</strong><br>
                ${window.Formatters.escapeHTML(a.address_line1)}${a.address_line2 ? ', ' + window.Formatters.escapeHTML(a.address_line2) : ''}, ${window.Formatters.escapeHTML(a.city)}, ${window.Formatters.escapeHTML(a.state)} - ${window.Formatters.escapeHTML(a.postal_code)}<br>
                <span style="font-size:.76rem; color:var(--admin-ink-soft);">Phone: ${window.Formatters.escapeHTML(a.phone)}</span>
              </div>
            `;
          }).join("");
        } else {
          addressBox.innerHTML = `<span style="color:var(--admin-ink-soft);">No saved address records available.</span>`;
        }
      }

      // Render Orders
      if (ordersBody) {
        const ordersRes = await window.AdminAPI.getCustomerOrders(cust.id);
        const custOrders = (ordersRes.success && ordersRes.data) ? ordersRes.data : (cust.recent_orders || []);

        if (custOrders.length === 0) {
          ordersBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2em; color:var(--admin-ink-soft);">No orders placed by this customer yet.</td></tr>`;
        } else {
          ordersBody.innerHTML = custOrders.map(function(o) {
            return `
              <tr>
                <td style="font-weight:600;">#${o.order_number}</td>
                <td style="color:var(--admin-ink-soft); font-size:.82rem;">${o.created_at ? o.created_at.split('T')[0] : 'Recent'}</td>
                <td style="font-weight:600;">${window.Formatters.formatINR(o.total_amount || 0)}</td>
                <td><span class="status-pill success">${o.order_status || 'Pending'}</span></td>
                <td style="text-align:right;">
                  <a href="order-details.html?id=${o.id}" class="btn-admin-secondary" style="padding:.2em .6em; font-size:.76rem; text-decoration:none;">View</a>
                </td>
              </tr>
            `;
          }).join("");
        }
      }

      // Render Payments
      if (paymentsBody) {
        const payRes = await window.AdminAPI.getCustomerPayments(cust.id);
        const payments = (payRes.success && payRes.data) ? payRes.data : [];
        if (payments.length === 0) {
          paymentsBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5em; color:var(--admin-ink-soft);">No payment transactions found.</td></tr>`;
        } else {
          paymentsBody.innerHTML = payments.map(function(p) {
            return `
              <tr>
                <td style="font-size:.82rem;">${p.provider_payment_id || ('PAY_' + p.id)}</td>
                <td>${p.order_number ? '#' + p.order_number : ('Order #' + p.order_id)}</td>
                <td style="text-transform:uppercase; font-size:.82rem;">${p.payment_method}</td>
                <td style="font-weight:600;">${window.Formatters.formatINR(p.amount)}</td>
                <td><span class="status-pill ${p.status === 'captured' || p.status === 'paid' ? 'success' : 'pending'}">${p.status}</span></td>
              </tr>
            `;
          }).join("");
        }
      }

      // Render Cart
      if (cartBox) {
        const cartRes = await window.AdminAPI.getCustomerCart(cust.id);
        const cartData = (cartRes.success && cartRes.data) ? cartRes.data : { items: [] };
        const cartItems = cartData.items || [];
        if (cartItems.length === 0) {
          cartBox.innerHTML = `<span style="color:var(--admin-ink-soft);">Customer cart is currently empty.</span>`;
        } else {
          cartBox.innerHTML = cartItems.map(function(item) {
            return `
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5em; padding-bottom:.5em; border-bottom:1px solid #f0f0f0;">
                <div>
                  <strong>${window.Formatters.escapeHTML(item.product_name)}</strong><br>
                  <span style="font-size:.76rem; color:var(--admin-ink-soft);">Qty: ${item.quantity} × ${window.Formatters.formatINR(item.price)}</span>
                </div>
                <strong style="color:var(--admin-gold);">${window.Formatters.formatINR(item.subtotal)}</strong>
              </div>
            `;
          }).join("") + `<div style="text-align:right; font-weight:600; margin-top:.5em;">Cart Total: ${window.Formatters.formatINR(cartData.cart_total || 0)}</div>`;
        }
      }

      // Render Wishlist
      if (wishlistBox) {
        const wishRes = await window.AdminAPI.getCustomerWishlist(cust.id);
        const wishItems = (wishRes.success && wishRes.data) ? wishRes.data : [];
        if (wishItems.length === 0) {
          wishlistBox.innerHTML = `<span style="color:var(--admin-ink-soft);">Customer wishlist is empty.</span>`;
        } else {
          wishlistBox.innerHTML = wishItems.map(function(item) {
            return `
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5em; padding-bottom:.5em; border-bottom:1px solid #f0f0f0;">
                <div>
                  <strong>${window.Formatters.escapeHTML(item.product_name)}</strong><br>
                  <span style="font-size:.76rem; color:var(--admin-ink-soft);">${item.in_stock ? 'In Stock' : 'Out of Stock'}</span>
                </div>
                <strong>${window.Formatters.formatINR(item.price)}</strong>
              </div>
            `;
          }).join("");
        }
      }

      // Render Search Activity
      if (searchBox) {
        const searchRes = await window.AdminAPI.getCustomerSearchHistory(cust.id);
        const searches = (searchRes.success && searchRes.data) ? searchRes.data : [];
        if (searches.length === 0) {
          searchBox.innerHTML = `<span style="color:var(--admin-ink-soft);">No search activity recorded yet.</span>`;
        } else {
          searchBox.innerHTML = searches.slice(0, 10).map(function(s) {
            return `
              <div style="display:flex; justify-content:space-between; margin-bottom:.4em;">
                <span>"${window.Formatters.escapeHTML(s.query)}"</span>
                <span style="font-size:.76rem; color:var(--admin-ink-soft);">${s.results_count} results · ${s.created_at ? s.created_at.split('T')[0] : ''}</span>
              </div>
            `;
          }).join("");
        }
      }

      // Render Reviews
      if (reviewsBox) {
        const revRes = await window.AdminAPI.getCustomerReviews(cust.id);
        const reviews = (revRes.success && revRes.data) ? revRes.data : [];
        if (reviews.length === 0) {
          reviewsBox.innerHTML = `<span style="color:var(--admin-ink-soft);">No product reviews submitted yet.</span>`;
        } else {
          reviewsBox.innerHTML = reviews.map(function(r) {
            return `
              <div style="margin-bottom:.6em; padding-bottom:.5em; border-bottom:1px solid #f0f0f0;">
                <div style="display:flex; justify-content:space-between;">
                  <strong>${window.Formatters.escapeHTML(r.product_name)}</strong>
                  <span class="status-pill ${r.status === 'approved' ? 'success' : 'pending'}" style="font-size:.7rem;">${r.status}</span>
                </div>
                <div style="color:var(--admin-gold); font-size:.8rem;">${'★'.repeat(r.rating || 5)}</div>
                <p style="margin:.2em 0 0; font-size:.8rem; color:var(--admin-ink-soft);">${window.Formatters.escapeHTML(r.comment || '')}</p>
              </div>
            `;
          }).join("");
        }
      }

      // Render Login Logs
      if (loginLogsBox) {
        const logRes = await window.AdminAPI.getCustomerLoginLogs(cust.id);
        const logs = (logRes.success && logRes.data) ? logRes.data : [];
        if (logs.length === 0) {
          loginLogsBox.innerHTML = `<span style="color:var(--admin-ink-soft);">No login activity logged.</span>`;
        } else {
          loginLogsBox.innerHTML = logs.slice(0, 10).map(function(l) {
            return `
              <div style="display:flex; justify-content:space-between; margin-bottom:.3em; font-size:.8rem;">
                <span>${l.login_at ? l.login_at.replace('T', ' ').split('.')[0] : 'Recent'} (${l.ip_address || 'IP N/A'})</span>
                <span class="status-pill ${l.success ? 'success' : 'alert'}" style="font-size:.7rem;">${l.success ? 'Success' : 'Failed'}</span>
              </div>
            `;
          }).join("");
        }
      }

    } catch (err) {
      console.error("Failed to load customer profile details:", err);
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    renderCustomersTable();
    renderCustomerDetailsPage();

    const searchInput = document.getElementById("adminCustomerSearch");
    const statusSelect = document.getElementById("adminCustomerStatusFilter");

    if (searchInput) searchInput.addEventListener("input", window.Helpers ? window.Helpers.debounce(function() { renderCustomersTable(); }, 300) : function() { renderCustomersTable(); });
    if (statusSelect) statusSelect.addEventListener("change", function() { renderCustomersTable(); });
  });
})();
