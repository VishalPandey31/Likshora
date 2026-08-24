/* =========================================================
   LIKSHORA — Customer Dedicated Cart Page Controller
   LocalStorage cart state, item quantities, promo code & checkout
   ========================================================= */

(function() {
  const CART_KEY = "rv_cart";
  let cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];
  let discountPercentage = 0;
  let appliedPromoCode = "";

  function saveCart() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(CART_KEY, cart);
      const user = window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null);
      if (user && user.email) {
        window.StorageUtils.writeJSON("rv_cart_" + user.email, cart);
      }
    }
  }

  function calculateSubtotal() {
    return cart.reduce(function(sum, item) {
      return sum + (item.price * item.qty);
    }, 0);
  }

  function calculateTotal() {
    const subtotal = calculateSubtotal();
    const discountAmount = Math.round(subtotal * (discountPercentage / 100));
    return Math.max(0, subtotal - discountAmount);
  }

  function renderCartPage() {
    cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : cart;
    const layoutEl = document.getElementById("cartPageLayout");
    const emptyNoticeEl = document.getElementById("cartEmptyNotice");
    const tableBody = document.getElementById("cartTableBody");
    const subtotalEl = document.getElementById("cartSubtotal");
    const discountRow = document.getElementById("cartDiscountRow");
    const discountEl = document.getElementById("cartDiscountVal");
    const totalEl = document.getElementById("cartTotalVal");

    if (!layoutEl || !emptyNoticeEl || !tableBody) return;

    if (cart.length === 0) {
      layoutEl.style.display = "none";
      emptyNoticeEl.classList.remove("hidden");
      if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(0);
      return;
    }

    layoutEl.style.display = "grid";
    emptyNoticeEl.classList.add("hidden");

    // Render Table Rows
    tableBody.innerHTML = cart.map(function(item) {
      let rawImg = item.image || (item.images && item.images.length > 0 ? (typeof item.images[0] === 'string' ? item.images[0] : item.images[0].url) : "");
      let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;

      const itemTotal = item.price * (item.qty || 1);

      return `
        <tr data-id="${item.id}" data-size="${item.size || 'M'}">
          <td>
            <div class="cart-item-info">
              <div class="cart-item-thumb">
                ${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(item.name) + '">' : ''}
              </div>
              <div>
                <h4 class="cart-item-name">${window.Formatters.escapeHTML(item.name)}</h4>
                <p class="cart-item-variant">Size: <strong>${item.size || 'M'}</strong>${item.color ? ' | Color: <strong>' + item.color + '</strong>' : ''}</p>
              </div>
            </div>
          </td>
          <td>${window.Formatters.formatINR(item.price)}</td>
          <td>
            <div class="cart-qty-ctrl" style="display:flex; align-items:center; gap:.4em;">
              <button type="button" class="qty-btn" data-action="down" style="width:24px; height:24px; border:1px solid var(--stone); background:none; border-radius:50%; cursor:pointer; display:inline-flex; align-items:center; justify-content:center;">-</button>
              <span style="font-size:.88rem; font-weight:500; min-width:18px; text-align:center;">${item.qty || 1}</span>
              <button type="button" class="qty-btn" data-action="up" style="width:24px; height:24px; border:1px solid var(--stone); background:none; border-radius:50%; cursor:pointer; display:inline-flex; align-items:center; justify-content:center;">+</button>
            </div>
          </td>
          <td style="font-weight: 600;">${window.Formatters.formatINR(itemTotal)}</td>
          <td style="text-align: right;">
            <button type="button" class="cart-remove-btn" data-action="remove">Remove</button>
          </td>
        </tr>
      `;
    }).join("");

    // Render Order Summary
    const subtotal = calculateSubtotal();
    const total = calculateTotal();
    const discountAmount = Math.round(subtotal * (discountPercentage / 100));

    if (subtotalEl) subtotalEl.textContent = window.Formatters.formatINR(subtotal);

    if (discountRow && discountEl) {
      if (discountPercentage > 0) {
        discountRow.classList.remove("hidden");
        discountEl.textContent = "– " + window.Formatters.formatINR(discountAmount);
      } else {
        discountRow.classList.add("hidden");
      }
    }

    if (totalEl) totalEl.textContent = window.Formatters.formatINR(total);

    // Update Header Badge
    const totalCount = cart.reduce(function(sum, item) { return sum + (item.qty || 1); }, 0);
    if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(totalCount);
  }

  function handleQuantityChange(id, size, delta) {
    const item = cart.find(function(i) { return i.id === id && (i.size || 'M') === size; });
    if (!item) return;

    item.qty += delta;
    if (item.qty <= 0) {
      cart = cart.filter(function(i) { return !(i.id === id && (i.size || 'M') === size); });
    }
    saveCart();
    if (typeof window.renderCart === "function") window.renderCart();
    renderCartPage();
  }

  function handleRemoveItem(id, size) {
    cart = cart.filter(function(i) { return !(i.id === id && (i.size || 'M') === size); });
    saveCart();
    if (typeof window.renderCart === "function") window.renderCart();
    renderCartPage();
    if (window.Toast) window.Toast.show("Item removed from cart");
  }



  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    renderCartPage();

    // Table click delegation for qty & remove buttons
    const tableBody = document.getElementById("cartTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", function(e) {
        const tr = e.target.closest("tr");
        if (!tr) return;
        const id = tr.dataset.id;
        const size = tr.dataset.size;

        const btn = e.target.closest("[data-action]");
        if (!btn) return;

        const action = btn.dataset.action;
        if (action === "up") handleQuantityChange(id, size, 1);
        if (action === "down") handleQuantityChange(id, size, -1);
        if (action === "remove") handleRemoveItem(id, size);
      });
    }



    // Proceed to Checkout
    const cartCheckoutBtn = document.getElementById("cartPageCheckoutBtn");
    if (cartCheckoutBtn) {
      cartCheckoutBtn.addEventListener("click", function() {
        if (cart.length === 0) return;
        const user = window.StorageUtils ? (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)) : null;
        if (!user) {
          window.location.href = "../auth/login.html";
        } else {
          window.location.href = "checkout.html";
        }
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
    const checkoutClose = document.getElementById("checkoutClose");
    if (checkoutClose) checkoutClose.addEventListener("click", function() { window.Modal.close("checkoutOverlay"); });
    const authGateClose = document.getElementById("authGateClose");
    if (authGateClose) authGateClose.addEventListener("click", function() { window.Modal.close("authGateOverlay"); });
    const placeOrderBtn = document.getElementById("placeOrderBtn");
    if (placeOrderBtn) {
      placeOrderBtn.addEventListener("click", function() {
        if (window.Toast) window.Toast.show("Order placed successfully!");
        cart = [];
        saveCart();
        renderCartPage();
        window.Modal.close("checkoutOverlay");
      });
    }

    window.addEventListener("storage", function(e) {
      if (e.key === CART_KEY || e.key === "rv_cart") {
        cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];
        renderCartPage();
      }
    });
  });
})();
