/* =========================================================
   LIKSHORA — Product Details Page Controller
   Dynamic PDP population, gallery switcher, size selection & related items
   ========================================================= */

(function() {
  const DEFAULT_EXTENDED_PRODUCTS = [];

  const storedProdList = window.StorageUtils ? window.StorageUtils.readJSON("rv_products", DEFAULT_EXTENDED_PRODUCTS) : DEFAULT_EXTENDED_PRODUCTS;
  const PRODUCTS = (storedProdList && storedProdList.length) ? storedProdList : DEFAULT_EXTENDED_PRODUCTS;

  let selectedSize = "M";
  let selectedQty = 1;
  const sizeQuantities = { S: 1, M: 1, L: 1, XL: 1, XXL: 1 };
  let currentProduct = null;
  let cart = [];
  let checkoutContext = null;
  let currentUser = window.StorageUtils ? window.StorageUtils.readJSON(window.RV_CONFIG ? window.RV_CONFIG.STORAGE_KEYS.USER : "rv_current_user", null) : null;

  function getProductIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id") || "AK01";
  }

  async function loadProductDetails() {
    const productId = getProductIdFromURL();
    if (window.ProductAPI && window.ProductAPI.getProductById) {
      try {
        const res = await window.ProductAPI.getProductById(productId);
        if (res.success && res.data) {
          currentProduct = res.data;
        }
      } catch (err) {
        console.warn("Could not fetch product details from API, using fallback:", err);
      }
    }

    if (!currentProduct) {
      currentProduct = PRODUCTS.find(function(p) { return String(p.id).trim() === String(productId).trim(); }) || null;
    }

    const sellingPrice = currentProduct.selling_price !== undefined ? currentProduct.selling_price : currentProduct.price;
    const listPrice = currentProduct.list_price !== undefined ? currentProduct.list_price : currentProduct.was;

    // Populate Breadcrumb & Titles
    const breadcrumbName = document.getElementById("pdpBreadcrumbName");
    const titleEl = document.getElementById("pdpTitle");
    const priceRow = document.getElementById("pdpPriceRow");
    const ratingStars = document.getElementById("pdpRatingStars");
    const ratingCount = document.getElementById("pdpRatingCount");
    const descEl = document.getElementById("pdpDescription");
    const mainImg = document.getElementById("pdpMainImg");
    const thumbStrip = document.getElementById("pdpThumbStrip");

    if (breadcrumbName) breadcrumbName.textContent = currentProduct.name;
    if (titleEl) titleEl.textContent = currentProduct.name;
    if (descEl) descEl.textContent = currentProduct.description || "Handpicked kurta in premium natural fabrics, engineered for everyday movement and long-lasting colour vibrancy.";

    // Price & Discount Calculation (Selling price vs List price)
    if (priceRow) {
      let priceHTML = '<span>' + window.Formatters.formatINR(sellingPrice) + '</span>';
      if (listPrice && listPrice > sellingPrice) {
        const savings = Math.round(((listPrice - sellingPrice) / listPrice) * 100);
        priceHTML += ' <span class="was">' + window.Formatters.formatINR(listPrice) + '</span>';
        priceHTML += ' <span class="pdp-discount-tag">' + savings + '% OFF</span>';
      }
      priceRow.innerHTML = priceHTML;
    }

    // Ratings
    if (ratingStars) ratingStars.textContent = "★".repeat(Math.floor(currentProduct.rating || 5));
    if (ratingCount) ratingCount.textContent = `(${currentProduct.reviews || 24} customer reviews)`;

    // Multi-Image Gallery Setup & Extraction
    let galleryImages = [];

    if (currentProduct.images && Array.isArray(currentProduct.images) && currentProduct.images.length > 0) {
      galleryImages = currentProduct.images.map(function(img) {
        let url = typeof img === 'string' ? img : (img.url || img);
        return window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(url, true) : url;
      }).filter(Boolean);
    } else if (currentProduct.image) {
      let rawImg = currentProduct.image;
      let baseImg = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;
      if (baseImg) galleryImages = [baseImg];
    }

    let activeImageIndex = 0;
    const galleryControls = document.getElementById("pdpGalleryControls");
    const navPrev = document.getElementById("pdpNavPrev");
    const navNext = document.getElementById("pdpNavNext");

    function updateMainImage(index) {
      if (galleryImages.length === 0) return;
      activeImageIndex = (index + galleryImages.length) % galleryImages.length;
      const targetSrc = galleryImages[activeImageIndex];

      if (mainImg) {
        mainImg.style.opacity = "0.2";
        setTimeout(function() {
          mainImg.src = targetSrc;
          mainImg.style.opacity = "1";
        }, 100);
      }

      if (thumbStrip) {
        thumbStrip.querySelectorAll(".thumb-btn").forEach(function(btn, i) {
          if (i === activeImageIndex) {
            btn.classList.add("active");
          } else {
            btn.classList.remove("active");
          }
        });
      }
    }

    // Render Thumbnail Boxes & Previous/Next Controls
    if (thumbStrip) {
      if (galleryImages.length <= 1) {
        thumbStrip.innerHTML = "";
        thumbStrip.style.display = "none";
        if (galleryControls) galleryControls.style.display = "none";
      } else {
        thumbStrip.style.display = "flex";
        thumbStrip.innerHTML = galleryImages.map(function(src, index) {
          return `
            <button type="button" class="thumb-btn ${index === 0 ? 'active' : ''}" data-index="${index}" aria-label="View Image ${index + 1}">
              <img src="${src}" alt="Thumbnail ${index + 1}">
            </button>
          `;
        }).join("");

        if (galleryControls) galleryControls.style.display = "flex";
      }
    }

    // Set initial image
    updateMainImage(0);

    // Thumbnail Click Event Listener
    if (thumbStrip) {
      thumbStrip.onclick = function(e) {
        const btn = e.target.closest(".thumb-btn");
        if (btn && btn.dataset.index !== undefined) {
          updateMainImage(parseInt(btn.dataset.index, 10));
        }
      };
    }

    renderRelatedProducts();
  }

  function renderRelatedProducts() {
    const grid = document.getElementById("relatedGrid");
    if (!grid || !currentProduct) return;

    const related = PRODUCTS.filter(function(p) { return p.id !== currentProduct.id; }).slice(0, 4);

    grid.innerHTML = related.map(function(p) {
      const priceHTML = p.was
        ? '<span class="was">' + window.Formatters.formatINR(p.was) + '</span>' + window.Formatters.formatINR(p.price)
        : window.Formatters.formatINR(p.price);

      let rawImg = p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].url) : "");
      let imgPath = window.Formatters && window.Formatters.formatProductImage
        ? window.Formatters.formatProductImage(rawImg, true)
        : (rawImg && !rawImg.startsWith("http") && !rawImg.startsWith("../") ? "../../" + rawImg : rawImg);

      return `
        <article class="product-card" data-id="${p.id}">
          <div class="product-media" onclick="window.location.href='product-details.html?id=${p.id}'" style="cursor:pointer;">
            ${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(p.name) + '" style="width:100%; height:100%; object-fit:cover; display:block;">' : '<div class="media-slot" data-placeholder="Product"></div>'}
            <div class="product-actions">
              <a href="product-details.html?id=${p.id}" class="product-btn buy-now">View Details</a>
            </div>
          </div>
          <h3 class="product-name"><a href="product-details.html?id=${p.id}">${window.Formatters.escapeHTML(p.name)}</a></h3>
          <p class="product-price">${priceHTML}</p>
        </article>
      `;
    }).join("");
  }

  function renderCart() {
    cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;
    const itemsWrap = document.getElementById("drawerItems");
    const totalEl = document.getElementById("drawerTotal");
    if (!itemsWrap || !totalEl) return;

    if (cart.length === 0) {
      itemsWrap.innerHTML = '<p class="drawer-empty" id="drawerEmpty">Your bag is empty — the edit is waiting.</p>';
    } else {
      itemsWrap.innerHTML = cart.map(function(item) {
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

    const total = cart.reduce(function(sum, item) { return sum + item.price * (item.qty || 1); }, 0);
    const count = cart.reduce(function(sum, item) { return sum + (item.qty || 1); }, 0);

    totalEl.textContent = window.Formatters.formatINR(total);
    if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(count);
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    loadProductDetails();

    document.querySelectorAll(".size-guide-link, #pdpSizeGuideBtn").forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        e.preventDefault();
        if (window.Modal && typeof window.Modal.openSizeGuide === "function") {
          window.Modal.openSizeGuide();
        }
      });
    });

    // Size Selection Matrix logic
    const sizeQtyList = document.getElementById("sizeQtyList");
    if (sizeQtyList) {
      sizeQtyList.addEventListener("click", function(e) {
        const row = e.target.closest(".size-qty-row");
        if (row) {
          document.querySelectorAll(".size-qty-row").forEach(function(r) { r.classList.remove("active"); });
          row.classList.add("active");
          selectedSize = row.dataset.size;
        }
      });
    }

    // Add to Cart button
    const pdpAddBtn = document.getElementById("pdpAddToCartBtn");
    if (pdpAddBtn) {
      pdpAddBtn.addEventListener("click", function() {
        if (!currentProduct) return;
        const stockQty = currentProduct.stock_quantity !== undefined ? currentProduct.stock_quantity : (currentProduct.stock !== undefined ? currentProduct.stock : 10);
        if (stockQty <= 0) {
          if (window.Toast) window.Toast.show("Sorry, this item is currently out of stock.");
          return;
        }
        const qty = 1;
        const itemToAdd = Object.assign({}, currentProduct, { qty: 1, size: selectedSize });

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
        const existing = localCart.find(function(i) { return i.id === currentProduct.id && (i.size || 'M') === selectedSize; });
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
        if (window.Modal && document.getElementById("cartDrawer")) {
          window.Modal.open("cartDrawer");
          const drawerOverlay = document.getElementById("drawerOverlay");
          if (drawerOverlay) drawerOverlay.classList.add("open");
        }
        if (window.Toast) window.Toast.show(`${currentProduct.name} (${selectedSize}) added to bag`);
      });
    }

    // Buy Now button - direct payment options flow
    const pdpBuyBtn = document.getElementById("pdpBuyNowBtn");
    if (pdpBuyBtn) {
      pdpBuyBtn.addEventListener("click", function() {
        if (!currentProduct) return;
        const qty = 1;
        checkoutContext = Object.assign({}, currentProduct, { qty: 1, size: selectedSize });
        
        const checkoutInfo = {
          contact: currentUser ? { name: currentUser.name, email: currentUser.email, phone: currentUser.phone } : { name: "Customer", email: "customer@example.com", phone: "9876543210" },
          address: { recipient: currentUser ? currentUser.name : "Valued Customer", street: "Flat 402, Lotus Apartments, MG Road", city: "Bengaluru", state: "Karnataka", pincode: "560001" },
          shippingFee: 0,
          subtotal: currentProduct.price * qty,
          grandTotal: currentProduct.price * qty,
          items: [checkoutContext]
        };

        if (window.StorageUtils) {
          window.StorageUtils.writeJSON("rv_buy_now_item", checkoutContext);
          window.StorageUtils.writeJSON("rv_checkout_info", checkoutInfo);
        }
        window.location.href = `checkout.html?buy_now=true&id=${currentProduct.id}&size=${selectedSize}&qty=1`;
      });
    }

    // Modals
    document.getElementById("navAboutBtn").addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    const navAboutBtnFooter = document.getElementById("navAboutBtnFooter");
    if (navAboutBtnFooter) navAboutBtnFooter.addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    document.getElementById("aboutClose").addEventListener("click", function() { window.Modal.close("aboutOverlay"); });

    document.getElementById("accountToggle").addEventListener("click", function() { window.Modal.open("accountOverlay"); });
    document.getElementById("accountClose").addEventListener("click", function() { window.Modal.close("accountOverlay"); });
    const drawerItems = document.getElementById("drawerItems");
    if (drawerItems) {
      drawerItems.addEventListener("click", function(e) {
        const up = e.target.closest("[data-qty-up]");
        const down = e.target.closest("[data-qty-down]");
        const remove = e.target.closest("[data-remove]");

        let localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;

        if (up) {
          const id = up.dataset.qtyUp;
          const size = up.dataset.size || 'M';
          const item = localCart.find(function(i) { return i.id === id && (i.size || 'M') === size; });
          if (item) { item.qty = (item.qty || 1) + 1; }
        }

        if (down) {
          const id = down.dataset.qtyDown;
          const size = down.dataset.size || 'M';
          const item = localCart.find(function(i) { return i.id === id && (i.size || 'M') === size; });
          if (item) {
            item.qty = (item.qty || 1) - 1;
            if (item.qty <= 0) {
              localCart = localCart.filter(function(i) { return !(i.id === id && (i.size || 'M') === size); });
            }
          }
        }

        if (remove) {
          const id = remove.dataset.remove;
          const size = remove.dataset.size || 'M';
          localCart = localCart.filter(function(i) { return !(i.id === id && (i.size || 'M') === size); });
        }

        cart = localCart;
        if (window.StorageUtils) {
          window.StorageUtils.writeJSON("rv_cart", cart);
        }
        renderCart();
      });
    }

    const cartClose = document.getElementById("cartClose");
    if (cartClose) cartClose.addEventListener("click", function() { window.Modal.close("cartDrawer"); document.getElementById("drawerOverlay").classList.remove("open"); });
    const drawerOverlay = document.getElementById("drawerOverlay");
    if (drawerOverlay) drawerOverlay.addEventListener("click", function() { window.Modal.close("cartDrawer"); drawerOverlay.classList.remove("open"); });
    const checkoutClose = document.getElementById("checkoutClose");
    if (checkoutClose) checkoutClose.addEventListener("click", function() { window.Modal.close("checkoutOverlay"); });
    const authGateClose = document.getElementById("authGateClose");
    if (authGateClose) authGateClose.addEventListener("click", function() { window.Modal.close("authGateOverlay"); });
    const authGateContinueGuest = document.getElementById("authGateContinueGuest");
    if (authGateContinueGuest) {
      authGateContinueGuest.addEventListener("click", function() {
        window.Modal.close("authGateOverlay");
        if (checkoutContext) {
          const modalTotal = document.getElementById("modalTotal");
          if (modalTotal) modalTotal.textContent = window.Formatters.formatINR(checkoutContext.price * checkoutContext.qty);
          window.Modal.open("checkoutOverlay");
        }
      });
    }
    const placeOrderBtn = document.getElementById("placeOrderBtn");
    if (placeOrderBtn) {
      placeOrderBtn.addEventListener("click", function() {
        window.Toast.show("Order placed successfully!");
        cart = [];
        renderCart();
        window.Modal.close("checkoutOverlay");
      });
    }
  });
})();
