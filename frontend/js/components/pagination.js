/* =========================================================
   LIKSHORA — Pagination Component
   Reusable pagination control for product grids and data tables
   ========================================================= */

window.Pagination = (function() {
  return {
    render: function(options) {
      const container = typeof options.containerId === "string" 
        ? document.getElementById(options.containerId) 
        : options.container;

      if (!container) return;

      const totalItems = options.totalItems || 0;
      const itemsPerPage = options.itemsPerPage || 8;
      const currentPage = options.currentPage || 1;
      const totalPages = Math.ceil(totalItems / itemsPerPage);

      if (totalPages <= 1) {
        container.innerHTML = "";
        return;
      }

      let html = `<div class="pagination-wrapper" style="display:flex; justify-content:center; align-items:center; gap:.5em; margin-top:2em;">`;

      // Previous button
      html += `<button type="button" class="btn btn-outline btn-sm" ${currentPage === 1 ? 'disabled style="opacity:0.5; cursor:default;"' : ''} data-page="${currentPage - 1}">&larr; Prev</button>`;

      // Page numbers
      for (let i = 1; i <= totalPages; i++) {
        const isActive = i === currentPage;
        html += `<button type="button" class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline'}" data-page="${i}">${i}</button>`;
      }

      // Next button
      html += `<button type="button" class="btn btn-outline btn-sm" ${currentPage === totalPages ? 'disabled style="opacity:0.5; cursor:default;"' : ''} data-page="${currentPage + 1}">Next &rarr;</button>`;

      html += `</div>`;

      container.innerHTML = html;

      // Attach event listeners
      container.querySelectorAll("button[data-page]").forEach(function(btn) {
        btn.addEventListener("click", function() {
          const page = parseInt(btn.dataset.page, 10);
          if (page >= 1 && page <= totalPages && page !== currentPage && typeof options.onPageChange === "function") {
            options.onPageChange(page);
          }
        });
      });
    }
  };
})();
