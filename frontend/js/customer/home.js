/* =========================================================
   LIKSHORA — Customer Home Page Script Logic
   Product catalog management, hero slider, category filters & cart
   ========================================================= */

(function() {
  // Use storage or default catalog fallback
  const PRODUCTS = window.StorageUtils.readJSON(
    window.RV_CONFIG.STORAGE_KEYS.PRODUCTS,
    window.RV_CONFIG.DEFAULT_PRODUCTS
  );

  let cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];
  let checkoutContext = null;
  let currentUser = window.StorageUtils.readJSON(window.RV_CONFIG.STORAGE_KEYS.USER, null);
  let activeCategory = "all";

  // Categories metadata
  const CATEGORIES = [];

  async function renderCategories() {
    const grid = document.getElementById("categoryGrid");
    if (!grid) return;

    let catList = CATEGORIES;
    if (window.ProductAPI && window.ProductAPI.getCategories) {
      try {
        const res = await window.ProductAPI.getCategories();
        if (res.success && res.data && Array.isArray(res.data)) {
          catList = res.data.map(function(c) {
            return {
              id: c.slug || c.id,
              name: c.name,
              count: c.description || "Explore Collection",
              image: c.image_url || c.image || "../../assets/images/products/product-kurti-1.jpg"
            };
          });
        }
      } catch (e) {
        console.warn("Could not fetch categories from API, using fallback:", e);
      }
    }

    grid.innerHTML = catList.map(function(cat) {
      return `
        <a href="pages/customer/products.html?category=${cat.id}" class="category-card" data-category="${cat.id}">
          <img src="${cat.image}" alt="${cat.name}">
          <div class="category-overlay">
            <h3 class="category-title">${cat.name}</h3>
            <p class="category-count">${cat.count}</p>
          </div>
        </a>
      `;
    }).join("");

    grid.addEventListener("click", function(e) {
      const card = e.target.closest("[data-category]");
      if (card) {
        const catId = card.dataset.category || card.getAttribute("data-category");
        if (catId) {
          window.location.href = `pages/customer/products.html?category=${encodeURIComponent(catId)}`;
        }
      }
    });
  }

  function updateActiveFilterButtons() {
    document.querySelectorAll(".tab-btn").forEach(function(btn) {
      btn.classList.toggle("active", btn.dataset.filter === activeCategory);
    });
  }

  const cardQuantities = {};

  async function renderProducts() {
    const grid = document.getElementById("productGrid");
    if (!grid) return;

    let productList = PRODUCTS;
    if (window.ProductAPI && window.ProductAPI.getProducts) {
      try {
        const res = await window.ProductAPI.getProducts({ category: activeCategory });
        if (res.success && res.data && Array.isArray(res.data.products)) {
          productList = res.data.products;
        }
      } catch (e) {
        console.warn("Could not fetch products from API, using fallback:", e);
      }
    }

    const filtered = activeCategory === "all"
      ? productList
      : productList.filter(function(p) { return p.category === activeCategory || (p.category_rel && p.category_rel.slug === activeCategory); });

    grid.innerHTML = filtered.map(function(p) {
      const pId = p.id;
      if (!cardQuantities[pId]) cardQuantities[pId] = 1;

      const sellingPrice = p.selling_price !== undefined ? p.selling_price : p.price;
      const listPrice = p.list_price !== undefined ? p.list_price : p.was;

      const priceHTML = listPrice && listPrice > sellingPrice
        ? '<span class="was">' + window.Formatters.formatINR(listPrice) + '</span>' + window.Formatters.formatINR(sellingPrice)
        : window.Formatters.formatINR(sellingPrice);

      let rawImg = p.image_url || p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].image_url || p.images[0].url) : "");
      let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;

      const mediaHTML = imgPath
        ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(p.name) + '">'
        : '<div class="media-slot" data-placeholder="Add product image"></div>';

      return `
        <article class="product-card" data-id="${pId}">
          <div class="product-media" onclick="window.location.href='pages/customer/product-details.html?id=${pId}'" style="cursor:pointer;">
            ${mediaHTML}
          </div>
          <h3 class="product-name" onclick="window.location.href='pages/customer/product-details.html?id=${pId}'" style="cursor:pointer;">${window.Formatters.escapeHTML(p.name)}</h3>
          <p class="product-price">${priceHTML}</p>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:.5em; margin-top:.8em;">
            <button type="button" class="btn btn-outline product-btn" data-add="${pId}" style="padding:.5em .3em; font-size:.76rem;">Add to Bag</button>
            <button type="button" class="btn btn-primary product-btn" data-buy="${pId}" style="padding:.5em .3em; font-size:.76rem;">Buy Now</button>
          </div>
        </article>
      `;
    }).join("");
  }

  function addToCart(id) {
    const product = PRODUCTS.find(function(p) { return String(p.id).trim() === String(id).trim(); });
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
      const loginPath = window.NavbarComponent && window.NavbarComponent.getLoginRedirectPath ? window.NavbarComponent.getLoginRedirectPath() : "pages/auth/login.html";
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
    openDrawer();
    if (window.Toast) window.Toast.show(product.name + " added to bag");
  }

  function buyNow(id) {
    const product = PRODUCTS.find(function(p) { return p.id === id; });
    if (!product) return;
    const qty = 1;
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
    window.location.href = `pages/customer/checkout.html?buy_now=true&id=${product.id}&qty=1`;
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
      : cart.reduce(function(sum, item) { return sum + item.price * item.qty; }, 0);
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

  function initHeroSlider() {
    const slides = Array.from(document.querySelectorAll(".hero-slide"));
    const dotsWrap = document.getElementById("heroDots");
    if (!slides.length || !dotsWrap) return;

    let index = 0;
    dotsWrap.innerHTML = "";
    slides.forEach(function(_, i) {
      const dot = document.createElement("button");
      dot.className = "hero-dot" + (i === 0 ? " active" : "");
      dot.addEventListener("click", function() { goTo(i); });
      dotsWrap.appendChild(dot);
    });

    const dots = Array.from(dotsWrap.children);

    function goTo(i) {
      slides[index].classList.remove("active");
      dots[index].classList.remove("active");
      index = (i + slides.length) % slides.length;
      slides[index].classList.add("active");
      dots[index].classList.add("active");
    }

    const prevBtn = document.getElementById("heroPrev");
    const nextBtn = document.getElementById("heroNext");
    if (prevBtn) prevBtn.addEventListener("click", function() { goTo(index - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function() { goTo(index + 1); });

    setInterval(function() { goTo(index + 1); }, 4500);
  }

  window.renderSearchResults = function(query) {
    const resultsWrap = document.getElementById("searchResults");
    if (!resultsWrap) return;
    const q = (query || "").trim().toLowerCase();
    if (!q) {
      resultsWrap.classList.remove("open");
      resultsWrap.innerHTML = "";
      return;
    }

    const matches = PRODUCTS.filter(function(p) { return p.name.toLowerCase().includes(q); });
    if (matches.length === 0) {
      resultsWrap.innerHTML = '<p class="search-no-results">No results found for “' + window.Formatters.escapeHTML(q) + '”.</p>';
      resultsWrap.classList.add("open");
      return;
    }

    resultsWrap.innerHTML = matches.map(function(p) {
      const priceHTML = p.was
        ? '<span class="was">' + window.Formatters.formatINR(p.was) + '</span>' + window.Formatters.formatINR(p.price)
        : window.Formatters.formatINR(p.price);

      let imgPath = p.image;
      if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
        imgPath = "../../" + imgPath;
      }

      return `
        <a href="product-details.html?id=${p.id}" class="search-result-item" style="text-decoration:none;">
          <span class="search-result-thumb">${imgPath ? '<img src="' + imgPath + '">' : ''}</span>
          <span class="search-result-name">${window.Formatters.escapeHTML(p.name)}</span>
          <span class="search-result-price">${priceHTML}</span>
        </a>
      `;
    }).join("");
    resultsWrap.classList.add("open");
  };

  async function syncWebsiteContent() {
    let siteContent = null;
    if (window.ProductAPI && window.ProductAPI.getSiteContent) {
      try {
        const res = await window.ProductAPI.getSiteContent();
        if (res.success && res.data) {
          siteContent = res.data;
        }
      } catch (e) {
        console.warn("Could not fetch site content from API, using fallback:", e);
      }
    }

    if (!siteContent && window.StorageUtils) {
      siteContent = window.StorageUtils.readJSON("rv_site_content", null);
    }

    if (!siteContent) return;

    // 1. Announcement Bar
    const announceEl = document.querySelector(".announce-bar p");
    const announceWrap = document.querySelector(".announce-bar");
    if (announceEl && siteContent.announcementText) {
      announceEl.textContent = siteContent.announcementText;
    }
    if (announceWrap) {
      announceWrap.style.display = siteContent.announcementActive === false ? "none" : "";
    }

    // 2. Hero Headline, Subtitle, CTA
    const heroH1 = document.querySelector(".hero-content h1");
    const heroSub = document.querySelector(".hero-content .hero-sub");
    const heroCta = document.querySelector(".hero-content .btn-primary");

    if (heroH1 && siteContent.heroTitle) {
      heroH1.innerHTML = window.Formatters ? window.Formatters.escapeHTML(siteContent.heroTitle) : siteContent.heroTitle;
    }
    if (heroSub && siteContent.heroSubtitle) {
      heroSub.textContent = siteContent.heroSubtitle;
    }
    if (heroCta && siteContent.heroCtaText) {
      heroCta.textContent = siteContent.heroCtaText;
    }

    // 3. Hero Slides
    if (siteContent.heroSlides && Array.isArray(siteContent.heroSlides) && siteContent.heroSlides.length > 0) {
      const heroSlidesWrap = document.getElementById("heroSlides");
      if (heroSlidesWrap) {
        heroSlidesWrap.innerHTML = siteContent.heroSlides.map(function(slide, idx) {
          let src = slide.image || slide.image_url;
          if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) {
            src = "../../" + src;
          }
          return `
            <div class="hero-slide ${idx === 0 ? 'active' : ''}">
              <img src="${src}" alt="${window.Formatters ? window.Formatters.escapeHTML(slide.caption || '') : (slide.caption || '')}">
            </div>
          `;
        }).join("");

        const dotsWrap = document.getElementById("heroDots");
        if (dotsWrap) {
          dotsWrap.innerHTML = siteContent.heroSlides.map(function(_, idx) {
            return `<button class="hero-dot ${idx === 0 ? 'active' : ''}" data-slide="${idx}"></button>`;
          }).join("");
        }
        initHeroSlider();
      }
    }

    // 4. Rotating Models Section (Marquee visual infinite loop track)
    if (siteContent.rotatingModels && Array.isArray(siteContent.rotatingModels) && siteContent.rotatingModels.length > 0) {
      const marqueeTrack = document.getElementById("marqueeTrack");
      if (marqueeTrack) {
        const slots = siteContent.rotatingModels.concat(siteContent.rotatingModels);
        marqueeTrack.innerHTML = slots.map(function(mod) {
          let src = mod.image || mod.image_url;
          if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) {
            src = "../../" + src;
          }
          return `
            <div class="marquee-slot">
              <img src="${src}" alt="${window.Formatters ? window.Formatters.escapeHTML(mod.name || '') : (mod.name || '')}">
            </div>
          `;
        }).join("");
      }
    }

    // 5. Footer Bio & Copyright
    const footerBio = document.querySelector(".footer-brand p");
    if (footerBio && siteContent.footerBrandBio) {
      footerBio.textContent = siteContent.footerBrandBio;
    }

    const footerCopyright = document.querySelector(".footer-bottom p");
    if (footerCopyright && siteContent.copyrightText) {
      footerCopyright.innerHTML = window.Formatters ? window.Formatters.escapeHTML(siteContent.copyrightText) : siteContent.copyrightText;
    }
  }

  window.addEventListener("storage", function(e) {
    if (e.key === "rv_site_content") {
      syncWebsiteContent();
    }
  });

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();
    syncWebsiteContent();
    renderCategories();
    renderProducts();
    renderCart();
    initHeroSlider();

    if (window.NavbarComponent) {
      window.NavbarComponent.updateUserAvatar(currentUser);
    }

    // Category Filter tab events
    document.querySelectorAll(".tab-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        activeCategory = btn.dataset.filter || "all";
        updateActiveFilterButtons();
        renderProducts();
      });
    });

    // Product Grid Action click handlers
    const gridEl = document.getElementById("productGrid");
    if (gridEl) {
      gridEl.addEventListener("click", function(e) {
        const up = e.target.closest("[data-qty-card-up]");
        const down = e.target.closest("[data-qty-card-down]");
        const addBtn = e.target.closest("[data-add]");
        const buyBtn = e.target.closest("[data-buy]");

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
      });
    }

    // Cart Drawer & Checkout triggers (if present)
    const cartClose = document.getElementById("cartClose");
    if (cartClose) cartClose.addEventListener("click", closeDrawer);
    const drawerOverlay = document.getElementById("drawerOverlay");
    if (drawerOverlay) {
      drawerOverlay.addEventListener("click", function() {
        closeDrawer();
        window.Modal.close("checkoutOverlay");
      });
    }

    const drawerItems = document.getElementById("drawerItems");
    if (drawerItems) {
      drawerItems.addEventListener("click", function(e) {
        const up = e.target.closest("[data-qty-up]");
        const down = e.target.closest("[data-qty-down]");
        const remove = e.target.closest("[data-remove]");

        let localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;

        if (up) {
          const id = up.dataset.qtyUp;
          const item = localCart.find(function(i) { return i.id === id; });
          if (item) { item.qty += 1; }
        }

        if (down) {
          const id = down.dataset.qtyDown;
          const item = localCart.find(function(i) { return i.id === id; });
          if (item) {
            item.qty -= 1;
            if (item.qty <= 0) {
              localCart = localCart.filter(function(i) { return i.id !== id; });
            }
          }
        }

        if (remove) {
          const id = remove.dataset.remove;
          localCart = localCart.filter(function(i) { return i.id !== id; });
        }

        cart = localCart;
        if (window.StorageUtils) {
          window.StorageUtils.writeJSON("rv_cart", cart);
        }
        renderCart();
      });
    }

    const checkoutBtn = document.getElementById("checkoutBtn");
    if (checkoutBtn) {
      checkoutBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const localCart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : cart;
        if (localCart.length === 0) {
          if (window.Toast) window.Toast.show("Your bag is empty");
          return;
        }
        const redirectPath = window.NavbarComponent && window.NavbarComponent.getCheckoutRedirectPath ? window.NavbarComponent.getCheckoutRedirectPath() : "pages/customer/checkout.html";
        window.location.href = redirectPath;
      });
    }

    const checkoutClose = document.getElementById("checkoutClose");
    if (checkoutClose) {
      checkoutClose.addEventListener("click", function() {
        window.Modal.close("checkoutOverlay");
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

    // Modal triggers
    document.getElementById("navAboutBtn").addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    const navAboutBtnFooter = document.getElementById("navAboutBtnFooter");
    if (navAboutBtnFooter) navAboutBtnFooter.addEventListener("click", function() { window.Modal.open("aboutOverlay"); });
    document.getElementById("aboutClose").addEventListener("click", function() { window.Modal.close("aboutOverlay"); });

    // Account modal triggers
    document.getElementById("accountToggle").addEventListener("click", function() { window.Modal.open("accountOverlay"); });
    document.getElementById("accountClose").addEventListener("click", function() { window.Modal.close("accountOverlay"); });

    // Auth gate triggers
    document.getElementById("authGateClose").addEventListener("click", function() { window.Modal.close("authGateOverlay"); });
    document.getElementById("authGateContinueGuest").addEventListener("click", function() {
      window.Modal.close("authGateOverlay");
      if (checkoutContext) {
        updateModalTotal();
        window.Modal.open("checkoutOverlay");
      }
    });
  });
})();
