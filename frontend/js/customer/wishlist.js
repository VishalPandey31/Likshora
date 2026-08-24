/* =========================================================
   LIKSHORA — Customer Wishlist Controller
   LocalStorage wishlist state, card rendering & move-to-cart
   ========================================================= */

(function() {
  const WISHLIST_KEY = "rv_wishlist";
  const CART_KEY = "rv_cart";

  const DEFAULT_EXTENDED_PRODUCTS = [
    { id: "AK01", name: "Rust Bell-Sleeve Printed Kurti", price: 2299, was: 2799, category: "kurtis", rating: 4.8, reviews: 34, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "AK02", name: "Maroon Paisley Kurti — Desi Edit", price: 2599, was: null, category: "kurtis", rating: 4.9, reviews: 42, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "SK01", name: "Black Printed Cami Kurti", price: 1499, was: null, category: "kurtis", rating: 4.6, reviews: 18, image: "../../assets/images/products/product-kurti-3.jpg" },
    { id: "SK02", name: "Black Bell-Sleeve V-Neck Kurti", price: 1699, was: 1999, category: "kurtis", rating: 4.7, reviews: 29, image: "../../assets/images/products/product-kurti-4.jpg" },
    { id: "KS01", name: "Aria Premium Long Kurti — Black Gold", price: 2899, was: null, category: "sets", rating: 5.0, reviews: 56, image: "../../assets/images/products/product-kurti-5.jpg" }
  ];

  const PRODUCTS = window.StorageUtils ? window.StorageUtils.readJSON(
    window.RV_CONFIG.STORAGE_KEYS.PRODUCTS,
    DEFAULT_EXTENDED_PRODUCTS
  ) : DEFAULT_EXTENDED_PRODUCTS;

  let wishlist = window.StorageUtils ? window.StorageUtils.readJSON(WISHLIST_KEY, ["AK01", "KS01"]) : ["AK01", "KS01"];
  let cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];

  function saveWishlist() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(WISHLIST_KEY, wishlist);
    }
  }

  function saveCart() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(CART_KEY, cart);
    }
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
          <button type="button" class="wishlist-btn active" data-remove-wishlist="${p.id}" aria-label="Remove from Wishlist">
            <svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-10-9.2C.4 8.1 2 4.5 5.6 4c2.1-.3 4 .8 6.4 3.5C14.4 4.8 16.3 3.7 18.4 4c3.6.5 5.2 4.1 3.6 7.8C19.5 16.4 12 21 12 21z"></path></svg>
          </button>
          ${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(p.name) + '">' : ''}
          <div class="product-actions">
            <button class="product-btn buy-now" data-move-cart="${p.id}">Move to Bag</button>
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

  function renderWishlistPage() {
    const grid = document.getElementById("wishlistGrid");
    const emptyNotice = document.getElementById("wishlistEmptyNotice");
    const countEl = document.getElementById("wishlistCount");

    if (!grid || !emptyNotice) return;

    const wishlistProducts = PRODUCTS.filter(function(p) {
      return wishlist.includes(p.id);
    });

    if (countEl) {
      countEl.textContent = `${wishlistProducts.length} ${wishlistProducts.length === 1 ? 'saved item' : 'saved items'}`;
    }

    if (wishlistProducts.length === 0) {
      grid.style.display = "none";
      emptyNotice.classList.remove("hidden");
      return;
    }

    grid.style.display = "grid";
    emptyNotice.classList.add("hidden");

    grid.innerHTML = wishlistProducts.map(renderProductCard).join("");
  }

  function moveToCart(id) {
    const product = PRODUCTS.find(function(p) { return p.id === id; });
    if (!product) return;

    const itemToAdd = Object.assign({}, product, { qty: 1, size: 'M' });

    let localCart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : cart;
    const existing = localCart.find(function(item) { return item.id === id && (item.size || 'M') === 'M'; });
    if (existing) {
      existing.qty = (existing.qty || 1) + 1;
    } else {
      localCart.push(itemToAdd);
    }
    cart = localCart;

    // Remove from wishlist
    wishlist = wishlist.filter(function(item) { return item !== id; });

    saveCart();
    const user = window.StorageUtils ? (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)) : null;
    if (user && user.email && window.StorageUtils) {
      window.StorageUtils.writeJSON("rv_cart_" + user.email, cart);
    }
    saveWishlist();
    renderWishlistPage();

    if (window.Toast) window.Toast.show(`${product.name} moved to bag!`);
  }

  function removeFromWishlist(id) {
    wishlist = wishlist.filter(function(item) { return item !== id; });
    saveWishlist();
    renderWishlistPage();
    if (window.Toast) window.Toast.show("Removed from wishlist");
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    renderWishlistPage();

    const grid = document.getElementById("wishlistGrid");
    if (grid) {
      grid.addEventListener("click", function(e) {
        const moveBtn = e.target.closest("[data-move-cart]");
        const removeBtn = e.target.closest("[data-remove-wishlist]");

        if (moveBtn) moveToCart(moveBtn.dataset.moveCart);
        if (removeBtn) removeFromWishlist(removeBtn.dataset.removeWishlist);
      });
    }

    // Modals
    const navAboutBtn = document.getElementById("navAboutBtn");
    if (navAboutBtn) navAboutBtn.addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    const navAboutBtnFooter = document.getElementById("navAboutBtnFooter");
    if (navAboutBtnFooter) navAboutBtnFooter.addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    const aboutClose = document.getElementById("aboutClose");
    if (aboutClose) aboutClose.addEventListener("click", function() { window.Modal.close("aboutOverlay"); });

    const accountClose = document.getElementById("accountClose");
    if (accountClose) accountClose.addEventListener("click", function() { window.Modal.close("accountOverlay"); });
    const cartClose = document.getElementById("cartClose");
    if (cartClose) cartClose.addEventListener("click", function() { window.Modal.close("cartDrawer"); document.getElementById("drawerOverlay").classList.remove("open"); });
    const drawerOverlay = document.getElementById("drawerOverlay");
    if (drawerOverlay) drawerOverlay.addEventListener("click", function() { window.Modal.close("cartDrawer"); document.getElementById("drawerOverlay").classList.remove("open"); });
  });
})();
