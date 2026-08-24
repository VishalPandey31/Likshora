/* =========================================================
   LIKSHORA — Admin Dashboard Analytics Controller
   Pure Vanilla JS & HTML/CSS analytics adapter for Admin Overview
   Structured so real API data endpoints can replace mock data later.
   ========================================================= */

window.AdminDashboardAdapter = (function() {
  return {
    getMetrics: async function(callback) {
      let metrics = {
        totalOrders: 0,
        totalCustomers: 0,
        totalProducts: 0,
        totalRevenue: 0,
        pendingOrdersCount: 0,
        deliveredOrdersCount: 0,
        revenueMonthlyTrend: [],
        lowStockProducts: [],
        recentOrders: []
      };

      if (window.AdminAPI && window.AdminAPI.getDashboardMetrics) {
        try {
          const res = await window.AdminAPI.getDashboardMetrics();
          if (res.success && res.data) {
            const data = res.data;
            metrics.totalOrders = data.total_orders !== undefined ? data.total_orders : data.totalOrders;
            metrics.totalCustomers = data.total_customers !== undefined ? data.total_customers : data.totalCustomers;
            metrics.totalProducts = data.total_products !== undefined ? data.total_products : data.totalProducts;
            metrics.totalRevenue = data.total_revenue !== undefined ? data.total_revenue : data.totalRevenue;
            metrics.pendingOrdersCount = data.pending_orders_count !== undefined ? data.pending_orders_count : data.pendingOrdersCount;
            metrics.deliveredOrdersCount = data.delivered_orders_count !== undefined ? data.delivered_orders_count : data.deliveredOrdersCount;
            metrics.lowStockProducts = data.low_stock_products || [];
            metrics.recentOrders = (data.recent_orders || []).map(function(o) {
              return {
                id: o.order_number || o.id,
                customer: o.user ? o.user.name : "Customer",
                date: o.created_at ? new Date(o.created_at).toLocaleDateString("en-IN") : "Today",
                total: o.total_amount || 0,
                status: o.order_status || "Processing",
                statusClass: (o.order_status === "delivered" || o.order_status === "Delivered") ? "success" : "pending"
              };
            });
          }
        } catch (e) {
          console.warn("Could not fetch metrics from AdminAPI:", e);
        }
      }

      if (typeof callback === "function") {
        callback(metrics);
      }
    }
  };
})();

(function() {
  function renderMetrics(data) {
    const totalOrdersEl = document.getElementById("metricTotalOrders");
    const totalCustomersEl = document.getElementById("metricTotalCustomers");
    const totalProductsEl = document.getElementById("metricTotalProducts");
    const totalRevenueEl = document.getElementById("metricTotalRevenue");

    if (totalOrdersEl) totalOrdersEl.textContent = data.totalOrders || 0;
    if (totalCustomersEl) totalCustomersEl.textContent = data.totalCustomers || 0;
    if (totalProductsEl) totalProductsEl.textContent = data.totalProducts || 0;
    if (totalRevenueEl) totalRevenueEl.textContent = window.Formatters ? window.Formatters.formatINR(data.totalRevenue || 0) : `₹${data.totalRevenue || 0}`;
  }

  function renderCSSBarChart(trendData) {
    const chartWrap = document.getElementById("revenueBarChartWrap");
    if (!chartWrap) return;

    if (!trendData || !Array.isArray(trendData) || trendData.length === 0) {
      chartWrap.innerHTML = `
        <div style="width:100%; text-align:center; color:var(--admin-ink-soft); font-size:.84rem; padding:3em 0;">
          No revenue trend data available yet
        </div>
      `;
      return;
    }

    chartWrap.innerHTML = trendData.map(function(item) {
      const formattedVal = window.Formatters ? window.Formatters.formatINR(item.value || 0) : `₹${item.value || 0}`;
      return `
        <div class="bar-group">
          <div class="bar-fill" style="height: ${item.heightPct || 0}%;" data-val="${formattedVal}"></div>
          <span class="bar-label">${window.Formatters ? window.Formatters.escapeHTML(item.month || "") : item.month}</span>
        </div>
      `;
    }).join("");
  }

  function renderFulfillmentProgress(data) {
    const total = data.totalOrders > 0 ? data.totalOrders : 0;
    const pendingCount = data.pendingOrdersCount || 0;
    const deliveredCount = data.deliveredOrdersCount || 0;

    const pendingPct = total > 0 ? Math.round((pendingCount / total) * 100) : 0;
    const deliveredPct = total > 0 ? Math.round((deliveredCount / total) * 100) : 0;

    const pendingBar = document.getElementById("progressPendingBar");
    const pendingVal = document.getElementById("progressPendingVal");
    const deliveredBar = document.getElementById("progressDeliveredBar");
    const deliveredVal = document.getElementById("progressDeliveredVal");

    if (pendingBar) pendingBar.style.width = pendingPct + "%";
    if (pendingVal) pendingVal.textContent = `${pendingCount} orders (${pendingPct}%)`;
    if (deliveredBar) deliveredBar.style.width = deliveredPct + "%";
    if (deliveredVal) deliveredVal.textContent = `${deliveredCount} orders (${deliveredPct}%)`;
  }

  function renderLowStockProducts(items) {
    const wrap = document.getElementById("lowStockListWrap");
    if (!wrap) return;

    if (!items || !Array.isArray(items) || items.length === 0) {
      wrap.innerHTML = `
        <div style="padding:1.5em 0; text-align:center; color:var(--admin-ink-soft); font-size:.84rem;">
          No low-stock alerts
        </div>
      `;
      return;
    }

    wrap.innerHTML = items.map(function(item) {
      return `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:.8em 0; border-bottom:1px solid var(--admin-border);">
          <div>
            <h4 style="margin:0; font-size:.9rem;">${window.Formatters ? window.Formatters.escapeHTML(item.name) : item.name}</h4>
            <span style="font-size:.76rem; color:var(--admin-ink-soft);">${item.category || ""} (ID: ${item.id || ""})</span>
          </div>
          <span class="status-pill alert">${item.stock} left in stock</span>
        </div>
      `;
    }).join("");
  }

  function renderRecentOrdersTable(orders) {
    const tableBody = document.getElementById("adminRecentOrdersTable");
    if (!tableBody) return;

    if (!orders || !Array.isArray(orders) || orders.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center; color:var(--admin-ink-soft); padding:1.5em;">
            No recent orders found
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = orders.map(function(order) {
      return `
        <tr>
          <td style="font-weight:600;">${window.Formatters ? window.Formatters.escapeHTML(order.id) : order.id}</td>
          <td>${window.Formatters ? window.Formatters.escapeHTML(order.customer) : order.customer}</td>
          <td style="color:var(--admin-ink-soft); font-size:.82rem;">${order.date || ""}</td>
          <td style="font-weight:600;">${window.Formatters ? window.Formatters.formatINR(order.total) : `₹${order.total}`}</td>
          <td><span class="status-pill ${order.statusClass || 'pending'}">${order.status || 'Pending'}</span></td>
          <td style="text-align:right;">
            <button class="btn-admin-secondary" style="padding:.3em .7em; font-size:.78rem;" data-view-order="${order.id}">View</button>
          </td>
        </tr>
      `;
    }).join("");

    tableBody.addEventListener("click", function(e) {
      const viewBtn = e.target.closest("[data-view-order]");
      if (viewBtn) {
        const orderId = viewBtn.dataset.viewOrder;
        if (window.Toast) window.Toast.show("Viewing order details for " + orderId);
      }
    });
  }

  function getCustomerLogins() {
    let stored = window.StorageUtils ? window.StorageUtils.readJSON("rv_customer_logins", null) : null;
    if (!stored || !Array.isArray(stored)) {
      return [];
    }
    // Filter out legacy sample demo data if present in localStorage
    const cleanLogins = stored.filter(function(item) {
      if (!item) return false;
      const email = item.userEmail || "";
      const id = item.id || "";
      if (email.includes("@example.com") || /^log_\d+$/.test(id)) {
        return false;
      }
      return true;
    });

    if (cleanLogins.length !== stored.length && window.StorageUtils) {
      window.StorageUtils.writeJSON("rv_customer_logins", cleanLogins);
    }
    return cleanLogins;
  }

  function renderCustomerLoginsGraph() {
    const logins = getCustomerLogins();
    const chartWrap = document.getElementById("loginBarChartWrap");
    const countEl = document.getElementById("totalLoginsCount");
    const tableBody = document.getElementById("adminCustomerLoginsTable");

    if (countEl) {
      countEl.textContent = `${logins.length} Total Logins`;
    }

    const daysOrder = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const dayCounts = { Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0, Sun: 0 };

    logins.forEach(function(l) {
      const d = l.dayOfWeek || "Mon";
      if (dayCounts[d] !== undefined) {
        dayCounts[d] += 1;
      }
    });

    const maxCount = Math.max(1, ...Object.values(dayCounts));

    if (chartWrap) {
      chartWrap.innerHTML = daysOrder.map(function(day) {
        const cnt = dayCounts[day];
        const heightPct = cnt > 0 ? Math.max(15, Math.round((cnt / maxCount) * 100)) : 0;
        const color = (cnt > 0 && cnt === maxCount) ? "var(--admin-gold)" : "var(--rust)";
        return `
          <div class="bar-group" style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end;">
            <span style="font-size:.76rem; font-weight:600; color:var(--admin-ink-soft); margin-bottom:.4em;">${cnt}</span>
            <div class="bar-fill" style="width:70%; height:${heightPct}%; background:${color}; border-radius:4px 4px 0 0; transition:all .3s ease;" title="${cnt} customer logins on ${day}"></div>
            <span class="bar-label" style="font-size:.78rem; font-weight:600; color:var(--admin-ink-soft); margin-top:.5em;">${day}</span>
          </div>
        `;
      }).join("");
    }

    if (tableBody) {
      if (logins.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align:center; color:var(--admin-ink-soft); padding:1.5em;">
              No customer login activity recorded yet
            </td>
          </tr>
        `;
      } else {
        tableBody.innerHTML = logins.slice(0, 5).map(function(item) {
          return `
            <tr>
              <td style="font-weight:600;">${window.Formatters ? window.Formatters.escapeHTML(item.userName) : item.userName}</td>
              <td style="color:var(--admin-ink-soft);">${window.Formatters ? window.Formatters.escapeHTML(item.userEmail) : item.userEmail}</td>
              <td style="font-size:.82rem; color:var(--admin-ink-soft);">${item.dateStr || item.timestamp}</td>
              <td style="font-weight:600; color:var(--admin-gold);">${item.dayOfWeek || "Mon"}</td>
              <td style="text-align:right;"><span class="status-pill success">Active Session</span></td>
            </tr>
          `;
        }).join("");
      }
    }
  }

  function initDashboardSliderTouch() {
    document.querySelectorAll(".dashboard-slider-box").forEach(function(box) {
      let isDown = false;
      let startX;
      let scrollLeft;

      box.addEventListener("mousedown", function(e) {
        isDown = true;
        box.style.cursor = "grabbing";
        startX = e.pageX - box.offsetLeft;
        scrollLeft = box.scrollLeft;
      });
      box.addEventListener("mouseleave", function() {
        isDown = false;
        box.style.cursor = "default";
      });
      box.addEventListener("mouseup", function() {
        isDown = false;
        box.style.cursor = "default";
      });
      box.addEventListener("mousemove", function(e) {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - box.offsetLeft;
        const walk = (x - startX) * 1.5;
        box.scrollLeft = scrollLeft - walk;
      });
    });
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
    window.AdminDashboardAdapter.getMetrics(function(metrics) {
      renderMetrics(metrics);
      renderCSSBarChart(metrics.revenueMonthlyTrend);
      renderCustomerLoginsGraph();
      renderFulfillmentProgress(metrics);
      renderLowStockProducts(metrics.lowStockProducts);
      renderRecentOrdersTable(metrics.recentOrders);
      initDashboardSliderTouch();
    });
  });
})();
