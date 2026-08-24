/* =========================================================
   LIKSHORA — Admin Product Reviews Controller
   Customer review listing, star rating, approval moderation & deletion
   ========================================================= */

(function() {
  let reviewsList = [];
  let pendingDeleteId = null;

  function renderStars(rating) {
    let stars = "";
    for (let i = 1; i <= 5; i++) {
      stars += i <= rating ? "★" : "☆";
    }
    return `<span style="color:var(--admin-gold); font-size:.9rem;">${stars} (${rating}.0)</span>`;
  }

  async function renderReviewsTable() {
    const tableBody = document.getElementById("adminReviewsTableBody");
    const countEl = document.getElementById("adminReviewsCount");
    if (!tableBody) return;

    const statusFilter = document.getElementById("adminReviewStatusFilter") ? document.getElementById("adminReviewStatusFilter").value : "all";

    try {
      const res = await window.AdminAPI.getAdminReviews({ status: statusFilter });
      if (res.success && res.data) {
        reviewsList = Array.isArray(res.data) ? res.data : [];
      } else {
        reviewsList = [];
      }

      if (countEl) countEl.textContent = `Showing ${reviewsList.length} customer reviews`;

      if (reviewsList.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No customer reviews match the selected filter.</td></tr>`;
        return;
      }

      tableBody.innerHTML = reviewsList.map(function(r) {
        let imgPath = r.product_image;
        if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
          imgPath = "../../" + imgPath;
        }

        const statusStr = (r.status || 'pending').toLowerCase();
        let statusDisplay = "Pending Approval";
        let statusPillClass = "pending";
        if (statusStr === "approved") {
          statusDisplay = "Approved";
          statusPillClass = "success";
        } else if (statusStr === "rejected") {
          statusDisplay = "Rejected";
          statusPillClass = "alert";
        }

        const dateStr = r.created_at ? r.created_at.split('T')[0] : 'Recent';

        return `
          <tr data-id="${r.id}">
            <td style="min-width:200px;">
              <div style="display:flex; align-items:center; gap:1em;">
                <div style="width:36px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
                  ${imgPath ? '<img src="' + imgPath + '" style="width:100%; height:100%; object-fit:cover;">' : ''}
                </div>
                <strong style="font-size:.86rem;">${window.Formatters.escapeHTML(r.product_name || 'Product')}</strong>
              </div>
            </td>
            <td>
              <strong style="font-size:.86rem;">${window.Formatters.escapeHTML(r.customer_name || 'Customer')}</strong>
              <p style="margin:0; font-size:.74rem; color:var(--admin-ink-soft);">${r.customer_email || ''}</p>
            </td>
            <td>${renderStars(r.rating || 5)}</td>
            <td style="max-width:280px; font-size:.84rem; color:var(--admin-ink-soft); line-height:1.4;">
              "${window.Formatters.escapeHTML(r.comment || '')}"
              <div style="font-size:.74rem; margin-top:2px;">${dateStr}</div>
            </td>
            <td><span class="status-pill ${statusPillClass}">${statusDisplay}</span></td>
            <td style="text-align:right;">
              <div style="display:flex; gap:.4em; justify-content:flex-end;">
                <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-toggle-review="${r.id}" data-current-status="${statusStr}">
                  ${statusStr === 'approved' ? 'Reject' : 'Approve'}
                </button>
                <button type="button" class="btn-admin-danger" style="padding:.3em .6em; font-size:.76rem;" data-delete-review="${r.id}">Delete</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      console.error("Failed to fetch admin reviews:", err);
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:2em; color:var(--admin-danger);">Failed to load customer reviews.</td></tr>`;
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    renderReviewsTable();

    const statusSelect = document.getElementById("adminReviewStatusFilter");
    if (statusSelect) statusSelect.addEventListener("change", function() { renderReviewsTable(); });

    const tableBody = document.getElementById("adminReviewsTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", async function(e) {
        const toggleBtn = e.target.closest("[data-toggle-review]");
        const deleteBtn = e.target.closest("[data-delete-review]");

        if (toggleBtn) {
          const id = toggleBtn.dataset.toggleReview;
          const currentStatus = toggleBtn.dataset.currentStatus;
          const nextStatus = currentStatus === "approved" ? "rejected" : "approved";

          try {
            const res = await window.AdminAPI.updateReviewStatus(id, nextStatus);
            if (res.success) {
              if (window.Toast) window.Toast.show(`Review status updated to ${nextStatus}`);
              renderReviewsTable();
            } else {
              if (window.Toast) window.Toast.show(res.message || "Failed to update status");
            }
          } catch (err) {
            console.error("Failed to update review status:", err);
          }
        }

        if (deleteBtn) {
          pendingDeleteId = deleteBtn.dataset.deleteReview;
          if (window.Modal) window.Modal.open("adminConfirmModal");
        }
      });
    }

    const confirmActionBtn = document.getElementById("adminConfirmModalActionBtn");
    if (confirmActionBtn) {
      confirmActionBtn.addEventListener("click", async function() {
        if (pendingDeleteId) {
          try {
            const res = await window.AdminAPI.deleteReview(pendingDeleteId);
            if (res.success) {
              if (window.Toast) window.Toast.show("Review deleted successfully.");
              renderReviewsTable();
            } else {
              if (window.Toast) window.Toast.show(res.message || "Failed to delete review");
            }
          } catch (err) {
            console.error("Failed to delete review:", err);
          } finally {
            if (window.Modal) window.Modal.close("adminConfirmModal");
            pendingDeleteId = null;
          }
        }
      });
    }
  });
})();
