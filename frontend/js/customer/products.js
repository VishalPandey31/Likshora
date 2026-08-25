/* =========================================================
   LIKSHORA — Customer Product Discovery Controller
   Filtering, sorting, wishlist state, pagination & product cards
   ========================================================= */

(function () {
  // Enhanced static products collection with ratings
  const DEFAULT_EXTENDED_PRODUCTS = [
    { id: "AK01", name: "Rust Bell-Sleeve Printed Kurti", price: 2299, was: 2799, category: "kurtis", rating: 4.8, reviews: 34, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "AK02", name: "Maroon Paisley Kurti — Desi Edit", price: 2599, was: null, category: "kurtis", rating: 4.9, reviews: 42, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "SK01", name: "Black Printed Cami Kurti", price: 1499, was: null, category: "kurtis", rating: 4.6, reviews: 18, image: "../../assets/images/products/product-kurti-3.jpg" },
    { id: "SK02", name: "Black Bell-Sleeve V-Neck Kurti", price: 1699, was: 1999, category: "kurtis", rating: 4.7, reviews: 29, image: "../../assets/images/products/product-kurti-4.jpg" },
    { id: "KS01", name: "Aria Premium Long Kurti — Black Gold", price: 2899, was: null, category: "sets", rating: 5.0, reviews: 56, image: "../../assets/images/products/product-kurti-5.jpg" },
    { id: "KS02", name: "Rust Bell-Sleeve Printed Kurti — Wine", price: 3299, was: 3799, category: "sets", rating: 4.9, reviews: 23, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "CK01", name: "Maroon Paisley Kurti — Blush Trim", price: 1399, was: null, category: "coords", rating: 4.5, reviews: 14, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "CK02", name: "Aria Premium Long Kurti — Teal Yoke", price: 1899, was: null, category: "coords", rating: 4.8, reviews: 38, image: "../../assets/images/products/product-kurti-5.jpg" },
    { id: "FK01", name: "Zari Embroidered Silk Kurta Set", price: 3999, was: 4599, category: "festive", rating: 4.9, reviews: 62, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "FK02", name: "Royal Velvet Kurti — Maroon Gold", price: 4299, was: null, category: "festive", rating: 5.0, reviews: 48, image: "../../assets/images/products/product-kurti-2.jpg" }
  ];

  const PRODUCTS = window.StorageUtils ? window.StorageUtils.readJSON(
    window.RV_CONFIG.STORAGE_KEYS.PRODUCTS,
    DEFAULT_EXTENDED_PRODUCTS
  ) : DEFAULT_EXTENDED_PRODUCTS;

  let globalFetchedProducts = PRODUCTS;

  let wishlistState = {};
  let currentPage = 1;
  const itemsPerPage = 8;
  let cart = [];
  let checkoutContext = null;
  let currentUser = window.StorageUtils ? window.StorageUtils.readJSON(window.RV_CONFIG.STORAGE_KEYS.USER, null) : null;

  // Read URL query parameters (?category=kurtis)
  function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      category: params.get("category") || "all",
      sort: params.get("sort") || "featured",
      search: params.get("search") || ""
    };
  }

  function renderProductCard(p) {
    const sellingPrice = p.selling_price !== undefined ? p.selling_price : p.price;
    const listPrice = p.list_price !== undefined ? p.list_price : (p.was !== undefined ? p.was : p.compare_at_price);

    let priceHTML = (listPrice && listPrice > sellingPrice)
      ? '<span class="was">' + window.Formatters.formatINR(listPrice) + '</span>' + window.Formatters.formatINR(sellingPrice)
      : window.Formatters.formatINR(sellingPrice);

    let rawImg = p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : (p.images[0].image_url || p.images[0].url)) : "");
    let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;

    const mediaHTML = imgPath
      ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(p.name) + '">'
      : '<div class="media-slot" data-placeholder="Add product image"></div>';

    const isWishlisted = Boolean(wishlistState[p.id]);
    if (!cardQuantities[p.id]) cardQuantities[p.id] = 1;
    const stockQty = p.stock_quantity !== undefined ? p.stock_quantity : (p.stock !== undefined ? p.stock : 10);
    const isOutOfStock = stockQty <= 0;

    return `
      <article class="product-card" data-id="${p.id}">
        <div class="product-media" onclick="window.location.href='product-details.html?id=${p.id}'" style="cursor:pointer; position:relative;">
          <button type="button" class="wishlist-btn ${isWishlisted ? 'active' : ''}" data-wishlist="${p.id}" aria-label="Toggle Wishlist">
            <svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-10-9.2C.4 8.1 2 4.5 5.6 4c2.1-.3 4 .8 6.4 3.5C14.4 4.8 16.3 3.7 18.4 4c3.6.5 5.2 4.1 3.6 7.8C19.5 16.4 12 21 12 21z"></path></svg>
          </button>
          ${mediaHTML}
          ${isOutOfStock ? '<span style="position:absolute; top:.6em; left:.6em; background:rgba(0,0,0,.75); color:#fff; font-size:.68rem; font-weight:600; padding:.2em .6em; border-radius:3px; text-transform:uppercase;">Out of Stock</span>' : ''}
        </div>
        <h3 class="product-name" onclick="window.location.href='product-details.html?id=${p.id}'" style="cursor:pointer;">${window.Formatters.escapeHTML(p.name)}</h3>
        <p class="product-price">${priceHTML}</p>
        <div class="product-rating">
          <span>★</span> <span>${p.rating || "4.8"}</span> <span style="color:var(--ink-soft); font-weight:normal;">(${p.reviews || "24"})</span>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:.5em; margin-top:.8em;">
          <button type="button" class="btn btn-outline product-btn" data-add="${p.id}" ${isOutOfStock ? 'disabled style="opacity:.5; cursor:not-allowed;"' : ''} style="padding:.5em .3em; font-size:.76rem;">${isOutOfStock ? 'Out of Stock' : 'Add to Bag'}</button>
          <button type="button" class="btn btn-primary product-btn" data-buy="${p.id}" ${isOutOfStock ? 'disabled style="opacity:.5; cursor:not-allowed;"' : ''} style="padding:.5em .3em; font-size:.76rem;">Buy Now</button>
        </div>
      </article>
    `;
  }

  function getFilteredAndSortedProducts() {
    const categoryFilter = document.getElementById("categoryFilter") ? document.getElementById("categoryFilter").value : "all";
    const sortValue = document.getElementById("sortSelect") ? document.getElementById("sortSelect").value : "featured";

    let list = PRODUCTS.slice();

    // Category Filter
    if (categoryFilter !== "all") {
      list = list.filter(function (p) {
        if (p.category) return p.category === categoryFilter;
        if (categoryFilter === "kurtis") return p.id.startsWith("AK") || p.id.startsWith("SK");
        if (categoryFilter === "sets") return p.id.startsWith("KS");
        if (categoryFilter === "coords") return p.id.startsWith("CK");
        if (categoryFilter === "festive") return p.id.startsWith("FK");
        return true;
      });
    }

    // Sorting
    if (sortValue === "price-asc") {
      list.sort(function (a, b) { return a.price - b.price; });
    } else if (sortValue === "price-desc") {
      list.sort(function (a, b) { return b.price - a.price; });
    } else if (sortValue === "newest") {
      list.reverse();
    }

    return list;
  }

  async function renderGrid() {
    const grid = document.getElementById("productGrid");
    const countEl = document.getElementById("resultsCount");
    if (!grid) return;

    if (window.Loader) window.Loader.show(grid);

    const categoryFilter = document.getElementById("categoryFilter") ? document.getElementById("categoryFilter").value : "all";
    const sortValue = document.getElementById("sortSelect") ? document.getElementById("sortSelect").value : "featured";

    let fetchedProducts = globalFetchedProducts;
    if (window.ProductAPI && window.ProductAPI.getProducts) {
      try {
        const res = await window.ProductAPI.getProducts({ category: categoryFilter, sort: sortValue });
        if (res.success && res.data) {
          if (Array.isArray(res.data)) {
            globalFetchedProducts = res.data;
          } else if (Array.isArray(res.data.products)) {
            globalFetchedProducts = res.data.products;
          }
          fetchedProducts = globalFetchedProducts;
        }
      } catch (err) {
        console.warn("Could not fetch products from REST API, using fallback:", err);
      }
    }

    let items = fetchedProducts.slice();
    if (categoryFilter !== "all") {
      items = items.filter(function (p) {
        if (p.category) return p.category === categoryFilter;
        if (p.category_rel && p.category_rel.slug) return p.category_rel.slug === categoryFilter;
        return true;
      });
    }

    if (sortValue === "price-asc") {
      items.sort(function (a, b) { return (a.selling_price || a.price) - (b.selling_price || b.price); });
    } else if (sortValue === "price-desc") {
      items.sort(function (a, b) { return (b.selling_price || b.price) - (a.selling_price || a.price); });
    }

    if (countEl) {
      countEl.textContent = `Showing ${items.length} ${items.length === 1 ? 'item' : 'items'}`;
    }

    if (items.length === 0) {
      grid.innerHTML = `
        <div class="empty-products-notice">
          <h3>No products found</h3>
          <p>Try adjusting your category filters or search keywords.</p>
        </div>
      `;
      const pagEl = document.getElementById("paginationContainer");
      if (pagEl) pagEl.innerHTML = "";
      return;
    }

    grid.innerHTML = items.map(renderProductCard).join("");

    const pagEl = document.getElementById("paginationContainer");
    if (pagEl) pagEl.innerHTML = "";
  }

  const cardQuantities = {};

  function findProductById(id) {
    if (!id) return null;
    const strId = String(id).trim();
    if (Array.isArray(globalFetchedProducts)) {
      const found = globalFetchedProducts.find(function (p) { return String(p.id).trim() === strId; });
      if (found) return found;
    }
    if (Array.isArray(PRODUCTS)) {
      const found = PRODUCTS.find(function (p) { return String(p.id).trim() === strId; });
      if (found) return found;
    }
    if (window.StorageUtils) {
      const stored = window.StorageUtils.readJSON("rv_products", []);
      if (Array.isArray(stored)) {
        const found = stored.find(function (p) { return String(p.id).trim() === strId; });
        if (found) return found;
      }
    }
    if (window.RV_CONFIG && Array.isArray(window.RV_CONFIG.DEFAULT_PRODUCTS)) {
      const found = window.RV_CONFIG.DEFAULT_PRODUCTS.find(function (p) { return String(p.id).trim() === strId; });
      if (found) return found;
    }
    return null;
  }

  function addToCart(id) {
    const product = findProductById(id);
    if (!product) return;

    const qty = 1;
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

    let localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];
    const existing = localCart.find(function (item) { return String(item.id).trim() === String(product.id).trim() && (item.size || 'M') === 'M'; });
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

    if (typeof window.renderCart === "function") window.renderCart();
    renderCart();
    openDrawer();
    if (window.Toast) window.Toast.show(product.name + " added to bag");
  }

  function buyNow(id) {
    const product = findProductById(id);
    if (!product) return;

    const checkoutContext = Object.assign({}, product, { qty: 1, size: 'M' });
    const checkoutInfo = {
      contact: { name: "Customer", email: "customer@example.com", phone: "9876543210" },
      address: { recipient: "Valued Customer", street: "Flat 402, Lotus Apartments, MG Road", city: "Bengaluru", state: "Karnataka", pincode: "560001" },
      shippingFee: 0,
      subtotal: product.price,
      grandTotal: product.price,
      items: [checkoutContext]
    };

    if (window.StorageUtils) {
      window.StorageUtils.writeJSON("rv_buy_now_item", checkoutContext);
      window.StorageUtils.writeJSON("rv_checkout_info", checkoutInfo);
    }

    window.location.href = `checkout.html?buy_now=true&id=${product.id}`;
  }

  function toggleWishlist(id) {
    const product = findProductById(id);
    if (!product) return;

    if (wishlistState[id]) {
      delete wishlistState[id];
      window.Toast.show("Removed from wishlist");
    } else {
      wishlistState[id] = true;
      window.Toast.show("Saved to wishlist");
    }

    renderGrid();
  }

  function renderCart() {
    cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;
    const itemsWrap = document.getElementById("drawerItems");
    const totalEl = document.getElementById("drawerTotal");

    if (!itemsWrap || !totalEl) return;

    if (cart.length === 0) {
      itemsWrap.innerHTML = '<p class="drawer-empty" id="drawerEmpty">Your bag is empty — the edit is waiting.</p>';
    } else {
      itemsWrap.innerHTML = cart.map(function (item) {
        let rawImg = item.image || (item.images && item.images.length > 0 ? (typeof item.images[0] === 'string' ? item.images[0] : item.images[0].url) : "");
        let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;
        let itemTotal = item.price * (item.qty || 1);

        return `
          <div class="drawer-item" data-id="${item.id}" data-size="${item.size || 'M'}">
            <div class="media-slot" data-placeholder="Product">${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(item.name) + '">' : ''}</div>
            <div class="drawer-item-info" style="display:flex; flex-direction:column; gap:.2em;">
              <p class="drawer-item-name" style="font-family:var(--font-display); font-size:.92rem; margin:0;">${window.Formatters.escapeHTML(item.name)}</p>
              ${item.size ? `<p class="drawer-item-size" style="font-size:.78rem; color:var(--ink-soft); margin:0;">Size: <strong>${item.size}</strong></p>` : ''}
              <p class="drawer-item-price" style="font-size:.8rem; color:var(--ink-soft); margin:0;">Price: ${window.Formatters.formatINR(item.price)}</p>
              <div class="drawer-item-qty" style="display:flex; align-items:center; gap:.4em; margin-top:.3em;">
                <button type="button" class="qty-btn" data-qty-down="${item.id}" data-size="${item.size || 'M'}">-</button>
                <span style="font-size:.82rem; font-weight:500;">Qty: ${item.qty || 1}</span>
                <button type="button" class="qty-btn" data-qty-up="${item.id}" data-size="${item.size || 'M'}">+</button>
              </div>
              <p class="drawer-item-total" style="font-size:.82rem; font-weight:600; color:var(--ink); margin-top:.2em;">Total: ${window.Formatters.formatINR(itemTotal)}</p>
            </div>
            <button class="drawer-item-remove" data-remove="${item.id}" data-size="${item.size || 'M'}">Remove</button>
          </div>
        `;
      }).join("");
    }

    const total = cart.reduce(function (sum, item) { return sum + item.price * (item.qty || 1); }, 0);
    const count = cart.reduce(function (sum, item) { return sum + (item.qty || 1); }, 0);

    totalEl.textContent = window.Formatters.formatINR(total);
    if (window.NavbarComponent) {
      window.NavbarComponent.updateCartBadge(count);
    }
    if (!checkoutContext) updateModalTotal();
  }

  function updateModalTotal() {
    const modalTotalEl = document.getElementById("modalTotal");
    if (!modalTotalEl) return;
    const total = checkoutContext
      ? checkoutContext.price * checkoutContext.qty
      : cart.reduce(function (sum, item) { return sum + item.price * item.qty; }, 0);
    modalTotalEl.textContent = window.Formatters.formatINR(total);
  }

  function openDrawer() {
    renderCart();
    window.Modal.open("cartDrawer");
    document.getElementById("drawerOverlay").classList.add("open");
  }

  function closeDrawer() {
    window.Modal.close("cartDrawer");
    document.getElementById("drawerOverlay").classList.remove("open");
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    // Parse URL params
    const query = getQueryParams();

    const categorySelect = document.getElementById("categoryFilter");
    const sortSelect = document.getElementById("sortSelect");

    if (categorySelect && query.category) {
      categorySelect.value = query.category;
    }
    if (sortSelect && query.sort) {
      sortSelect.value = query.sort;
    }

    renderGrid();
    renderCart();

    if (categorySelect) {
      categorySelect.addEventListener("change", function () {
        currentPage = 1;
        renderGrid();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener("change", function () {
        currentPage = 1;
        renderGrid();
      });
    }



    // Grid Click Delegation
    const grid = document.getElementById("productGrid");
    if (grid) {
      grid.addEventListener("click", function (e) {
        const up = e.target.closest("[data-qty-card-up]");
        const down = e.target.closest("[data-qty-card-down]");
        const addBtn = e.target.closest("[data-add]");
        const buyBtn = e.target.closest("[data-buy]");
        const wishBtn = e.target.closest("[data-wishlist]");

        if (up) {
          e.stopPropagation();
          const id = up.dataset.qtyCardUp;
          cardQuantities[id] = (cardQuantities[id] || 1) + 1;
          const valEl = document.getElementById("cardQtyVal_" + id);
          if (valEl) valEl.textContent = cardQuantities[id];
        }

        if (down) {
          e.stopPropagation();
          const id = down.dataset.qtyCardDown;
          let q = cardQuantities[id] || 1;
          if (q > 1) q -= 1;
          cardQuantities[id] = q;
          const valEl = document.getElementById("cardQtyVal_" + id);
          if (valEl) valEl.textContent = q;
        }

        if (addBtn) {
          e.stopPropagation();
          addToCart(addBtn.dataset.add);
        }

        if (buyBtn) {
          e.stopPropagation();
          buyNow(buyBtn.dataset.buy);
        }

        if (wishBtn) {
          e.stopPropagation();
          toggleWishlist(wishBtn.dataset.wishlist);
        }
      });
    }

    // Cart drawer interactions
    document.getElementById("cartToggle").addEventListener("click", openDrawer);
    document.getElementById("cartClose").addEventListener("click", closeDrawer);
    document.getElementById("drawerOverlay").addEventListener("click", function () {
      closeDrawer();
      window.Modal.close("checkoutOverlay");
    });

    document.getElementById("drawerItems").addEventListener("click", function (e) {
      const up = e.target.closest("[data-qty-up]");
      const down = e.target.closest("[data-qty-down]");
      const remove = e.target.closest("[data-remove]");

      let localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;

      if (up) {
        const id = up.dataset.qtyUp;
        const size = up.dataset.size || 'M';
        const item = localCart.find(function (i) { return i.id === id && (i.size || 'M') === size; });
        if (item) { item.qty = (item.qty || 1) + 1; }
      }

      if (down) {
        const id = down.dataset.qtyDown;
        const size = down.dataset.size || 'M';
        const item = localCart.find(function (i) { return i.id === id && (i.size || 'M') === size; });
        if (item) {
          item.qty = (item.qty || 1) - 1;
          if (item.qty <= 0) {
            localCart = localCart.filter(function (i) { return !(i.id === id && (i.size || 'M') === size); });
          }
        }
      }

      if (remove) {
        const id = remove.dataset.remove;
        const size = remove.dataset.size || 'M';
        localCart = localCart.filter(function (i) { return !(i.id === id && (i.size || 'M') === size); });
      }

      cart = localCart;
      if (window.StorageUtils) {
        window.StorageUtils.writeJSON("rv_cart", cart);
      }
      renderCart();
    });

    // Checkout modal triggers
    const checkoutBtn = document.getElementById("checkoutBtn");
    if (checkoutBtn) {
      checkoutBtn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;
        if (localCart.length === 0) {
          if (window.Toast) window.Toast.show("Your bag is empty");
          return;
        }
        const redirectPath = window.NavbarComponent && window.NavbarComponent.getCheckoutRedirectPath ? window.NavbarComponent.getCheckoutRedirectPath() : "checkout.html";
        window.location.href = redirectPath;
      });
    }

    document.getElementById("checkoutClose").addEventListener("click", function () {
      window.Modal.close("checkoutOverlay");
    });

    document.getElementById("placeOrderBtn").addEventListener("click", function () {
      window.Toast.show("Order placed successfully!");
      cart = [];
      renderCart();
      window.Modal.close("checkoutOverlay");
    });

    // About & Account Modals
    document.getElementById("navAboutBtn").addEventListener("click", function () { window.Modal.open("aboutOverlay"); });
    const navAboutBtnFooter = document.getElementById("navAboutBtnFooter");
    if (navAboutBtnFooter) navAboutBtnFooter.addEventListener("click", function () { window.Modal.open("aboutOverlay"); });
    document.getElementById("aboutClose").addEventListener("click", function () { window.Modal.close("aboutOverlay"); });

    document.getElementById("accountToggle").addEventListener("click", function () { window.Modal.open("accountOverlay"); });
    document.getElementById("accountClose").addEventListener("click", function () { window.Modal.close("accountOverlay"); });

    document.getElementById("authGateClose").addEventListener("click", function () { window.Modal.close("authGateOverlay"); });
    document.getElementById("authGateContinueGuest").addEventListener("click", function () {
      window.Modal.close("authGateOverlay");
      if (checkoutContext) {
        updateModalTotal();
        window.Modal.open("checkoutOverlay");
      }
    });
  });
})();
