/* =========================================================
   LIKSHORA — Dedicated Search Page Controller
   Search query processing, filters, sorting & product grid
   ========================================================= */

(function() {
  const DEFAULT_EXTENDED_PRODUCTS = [
    { id: "AK01", name: "Rust Bell-Sleeve Printed Kurti", price: 2299, was: 2799, category: "kurtis", rating: 4.8, reviews: 34, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "AK02", name: "Maroon Paisley Kurti — Desi Edit", price: 2599, was: null, category: "kurtis", rating: 4.9, reviews: 42, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "SK01", name: "Black Printed Cami Kurti", price: 1499, was: null, category: "kurtis", rating: 4.6, reviews: 18, image: "../../assets/images/products/product-kurti-3.jpg" },
    { id: "SK02", name: "Black Bell-Sleeve V-Neck Kurti", price: 1699, was: 1999, category: "kurtis", rating: 4.7, reviews: 29, image: "../../assets/images/products/product-kurti-4.jpg" },
    { id: "KS01", name: "Aria Premium Long Kurti — Black Gold", price: 2899, was: null, category: "sets", rating: 5.0, reviews: 56, image: "../../assets/images/products/product-kurti-5.jpg" },
    { id: "KS02", name: "Rust Bell-Sleeve Printed Kurti — Wine", price: 3299, was: 3799, category: "sets", rating: 4.9, reviews: 23, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "CK01", name: "Maroon Paisley Kurti — Blush Trim", price: 1399, was: null, category: "coords", rating: 4.5, reviews: 14, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "CK02", name: "Aria Premium Long Kurti — Teal Yoke", price: 1899, was: null, category: "coords", rating: 4.8, reviews: 38, image: "../../assets/images/products/product-kurti-5.jpg" }
  ];

  const PRODUCTS = window.StorageUtils ? window.StorageUtils.readJSON(
    window.RV_CONFIG.STORAGE_KEYS.PRODUCTS,
    DEFAULT_EXTENDED_PRODUCTS
  ) : DEFAULT_EXTENDED_PRODUCTS;

  let currentPage = 1;
  const itemsPerPage = 8;
  let cart = [];
  let checkoutContext = null;
  let currentUser = window.StorageUtils ? window.StorageUtils.readJSON(window.RV_CONFIG.STORAGE_KEYS.USER, null) : null;

  function getSearchQueryFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("q") || "";
  }

  function renderProductCard(p) {
    const priceHTML = p.was
      ? '<span class="was">' + window.Formatters.formatINR(p.was) + '</span>' + window.Formatters.formatINR(p.price)
      : window.Formatters.formatINR(p.price);

    let rawImg = p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].url) : "");
    let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;

    return `
      <article class="product-card" data-id="${p.id}">
        <div class="product-media">
          ${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(p.name) + '">' : ''}
          <div class="product-actions">
            <a href="product-details.html?id=${p.id}" class="product-btn buy-now">View Details</a>
            <button class="product-btn add-cart" data-add="${p.id}">Add to Cart</button>
          </div>
        </div>
        <h3 class="product-name"><a href="product-details.html?id=${p.id}">${window.Formatters.escapeHTML(p.name)}</a></h3>
        <p class="product-price">${priceHTML}</p>
        <div class="product-rating">
          <span>★</span> <span>${p.rating || "4.8"}</span>
        </div>
      </article>
    `;
  }

  function executeSearch() {
    const inputEl = document.getElementById("searchPageInput");
    const query = inputEl ? inputEl.value.trim().toLowerCase() : "";
    const categoryFilter = document.getElementById("searchCategoryFilter") ? document.getElementById("searchCategoryFilter").value : "all";
    const sortValue = document.getElementById("searchSortSelect") ? document.getElementById("searchSortSelect").value : "featured";
    const grid = document.getElementById("searchResultsGrid");
    const countEl = document.getElementById("searchResultCount");

    if (!grid) return;

    let matches = PRODUCTS.filter(function(p) {
      const matchQuery = !query || p.name.toLowerCase().includes(query);
      const matchCat = categoryFilter === "all" || (p.category && p.category === categoryFilter);
      return matchQuery && matchCat;
    });

    if (sortValue === "price-asc") {
      matches.sort(function(a, b) { return a.price - b.price; });
    } else if (sortValue === "price-desc") {
      matches.sort(function(a, b) { return b.price - a.price; });
    }

    if (countEl) {
      countEl.textContent = `Found ${matches.length} ${matches.length === 1 ? 'result' : 'results'} ${query ? 'for “' + query + '”' : ''}`;
    }

    if (matches.length === 0) {
      grid.innerHTML = `
        <div class="empty-products-notice">
          <h3>No results found</h3>
          <p>We couldn't find anything matching your search term. Try searching for “kurti”, “paisley”, or “black”.</p>
        </div>
      `;
      if (window.Pagination) window.Pagination.render({ totalItems: 0, containerId: "searchPaginationContainer" });
      return;
    }

    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginated = matches.slice(startIndex, startIndex + itemsPerPage);

    grid.innerHTML = paginated.map(renderProductCard).join("");

    if (window.Pagination) {
      window.Pagination.render({
        totalItems: matches.length,
        itemsPerPage: itemsPerPage,
        currentPage: currentPage,
        containerId: "searchPaginationContainer",
        onPageChange: function(newPage) {
          currentPage = newPage;
          executeSearch();
          window.Helpers.scrollToElement(grid);
        }
      });
    }
  }

  function addToCart(id) {
    const product = PRODUCTS.find(function(p) { return String(p.id).trim() === String(id).trim(); });
    if (!product) return;

    const itemToAdd = Object.assign({}, product, { qty: 1, size: 'M' });

    const isLoggedIn = window.NavbarComponent && window.NavbarComponent.isLoggedIn
      ? window.NavbarComponent.isLoggedIn()
      : Boolean(window.StorageUtils && (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)));

    if (!isLoggedIn) {
      if (window.StorageUtils) {
        window.StorageUtils.writeJSON("rv_pending_add_to_bag", { item: itemToAdd, returnUrl: window.location.href });
      }
      const loginPath = window.NavbarComponent && window.NavbarComponent.getLoginRedirectPath ? window.NavbarComponent.getLoginRedirectPath() : "../auth/login.html";
      window.location.href = loginPath;
      return;
    }

    let localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;
    const existing = localCart.find(function(item) { return String(item.id).trim() === String(id).trim() && (item.size || 'M') === 'M'; });
    if (existing) {
      existing.qty = (existing.qty || 1) + 1;
    } else {
      localCart.push(itemToAdd);
    }
    cart = localCart;
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON("rv_cart", cart);
      const user = window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null);
      if (user && user.email) {
        window.StorageUtils.writeJSON("rv_cart_" + user.email, cart);
      }
    }
    renderCart();
    if (window.Toast) window.Toast.show(product.name + " added to bag");
    if (window.Modal && document.getElementById("cartDrawer")) {
      window.Modal.open("cartDrawer");
      const drawerOverlay = document.getElementById("drawerOverlay");
      if (drawerOverlay) drawerOverlay.classList.add("open");
    }
  }

  function renderCart() {
    const itemsWrap = document.getElementById("drawerItems");
    const totalEl = document.getElementById("drawerTotal");
    if (!itemsWrap || !totalEl) return;

    if (cart.length === 0) {
      itemsWrap.innerHTML = '<p class="drawer-empty">Your bag is empty — the edit is waiting.</p>';
    } else {
      itemsWrap.innerHTML = cart.map(function(item) {
        let imgPath = item.image;
        if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
          imgPath = "../../" + imgPath;
        }
        return `
          <div class="drawer-item" data-id="${item.id}">
            <div class="media-slot" data-placeholder="Product">${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(item.name) + '">' : ''}</div>
            <div>
              <p class="drawer-item-name">${window.Formatters.escapeHTML(item.name)}</p>
              <p class="drawer-item-price">${window.Formatters.formatINR(item.price)}</p>
            </div>
            <button class="drawer-item-remove" data-remove="${item.id}">Remove</button>
          </div>
        `;
      }).join("");
    }

    const total = cart.reduce(function(sum, item) { return sum + item.price * item.qty; }, 0);
    const count = cart.reduce(function(sum, item) { return sum + item.qty; }, 0);
    totalEl.textContent = window.Formatters.formatINR(total);
    if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(count);
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    const query = getSearchQueryFromURL();
    const inputEl = document.getElementById("searchPageInput");
    if (inputEl && query) {
      inputEl.value = query;
    }

    executeSearch();

    if (inputEl) {
      inputEl.addEventListener("input", window.Helpers.debounce(function() {
        currentPage = 1;
        executeSearch();
      }, 300));
    }

    const btnSubmit = document.getElementById("searchPageBtn");
    if (btnSubmit) {
      btnSubmit.addEventListener("click", function() {
        currentPage = 1;
        executeSearch();
      });
    }

    const categorySelect = document.getElementById("searchCategoryFilter");
    const sortSelect = document.getElementById("searchSortSelect");
    if (categorySelect) categorySelect.addEventListener("change", function() { currentPage = 1; executeSearch(); });
    if (sortSelect) sortSelect.addEventListener("change", function() { currentPage = 1; executeSearch(); });

    const grid = document.getElementById("searchResultsGrid");
    if (grid) {
      grid.addEventListener("click", function(e) {
        const addBtn = e.target.closest("[data-add]");
        if (addBtn) addToCart(addBtn.dataset.add);
      });
    }

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
