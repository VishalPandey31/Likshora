/* =========================================================
   LIKSHORA — Customer Checkout Address & Shipping Controller
   Address selection, saved addresses, delivery option & checkout data
   ========================================================= */

(function () {
  const CART_KEY = "rv_cart";
  const USER_KEY = "rv_current_user";
  const CHECKOUT_INFO_KEY = "rv_checkout_info";

  let cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];
  let currentUser = window.StorageUtils ? window.StorageUtils.readJSON(USER_KEY, null) : null;
  let selectedShippingFee = 0;

  const DEFAULT_ADDRESSES = [
    {
      id: "addr_1",
      name: "Customer Home",
      recipient: currentUser ? currentUser.name : "Ananya Sharma",
      phone: currentUser ? currentUser.phone : "9876543210",
      street: "Flat 402, Lotus Apartments, MG Road",
      city: "Bengaluru",
      state: "Karnataka",
      pincode: "560001"
    }
  ];

  let addresses = DEFAULT_ADDRESSES;
  let selectedAddressId = "addr_1";

  const DEFAULT_CATALOG = [
    { id: "AK01", sku: "AK01-RUST", name: "Rust Bell-Sleeve Printed Kurti", price: 2299, was: 2799, category: "kurtis", stock: 3, rating: 4.8, status: "Active", description: "Breathable 100% cotton printed kurti with bell sleeves.", image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "AK02", sku: "AK02-MRN", name: "Maroon Paisley Kurti — Desi Edit", price: 2599, was: null, category: "kurtis", stock: 12, rating: 4.9, status: "Active", description: "Rich burgundy maroon base with traditional paisley prints.", image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "SK01", sku: "SK01-BLK", name: "Black Printed Cami Kurti", price: 1499, was: null, category: "kurtis", stock: 2, rating: 4.6, status: "Active", description: "Sleek black cami-style kurti with ivory block prints.", image: "../../assets/images/products/product-kurti-3.jpg" },
    { id: "SK02", sku: "SK02-BLK", name: "Black Bell-Sleeve V-Neck Kurti", price: 1699, was: 1999, category: "kurtis", stock: 18, rating: 4.7, status: "Active", description: "Classic black V-neck framed by flared bell sleeves.", image: "../../assets/images/products/product-kurti-4.jpg" },
    { id: "KS01", sku: "KS01-GLD", name: "Aria Premium Long Kurti — Black Gold", price: 2899, was: null, category: "sets", stock: 8, rating: 5.0, status: "Active", description: "Floor-length black kurta with hand-applied gold zari foil print.", image: "../../assets/images/products/product-kurti-5.jpg" }
  ];

  // Check for direct Buy Now item
  const buyNowItem = window.StorageUtils ? window.StorageUtils.readJSON("rv_buy_now_item", null) : null;
  const urlParams = new URLSearchParams(window.location.search);
  const isBuyNowParam = urlParams.get("buy_now") === "true";
  const buyId = urlParams.get("id");
  const buySize = urlParams.get("size") || "M";
  const buyQty = parseInt(urlParams.get("qty") || "1", 10);

  if (isBuyNowParam) {
    if (buyNowItem && String(buyNowItem.id) === String(buyId)) {
      cart = [Object.assign({}, buyNowItem, { size: buySize, qty: buyQty })];
    } else {
      const storedProducts = window.StorageUtils ? window.StorageUtils.readJSON("rv_products", DEFAULT_CATALOG) : DEFAULT_CATALOG;
      const products = (storedProducts && storedProducts.length) ? storedProducts : DEFAULT_CATALOG;
      const found = products.find(function (p) { return String(p.id) === String(buyId); }) || products.find(function (p) { return p.id === buyId; });
      if (found) {
        cart = [Object.assign({}, found, { size: buySize, qty: buyQty })];
      } else if (buyNowItem) {
        cart = [buyNowItem];
      }
    }
  } else if (cart.length === 0 && buyNowItem) {
    cart = [buyNowItem];
  }

  if (cart.length === 0 && (buyNowItem || urlParams.get("buy_now") === "true")) {
    cart = [DEFAULT_CATALOG[0]];
  }

  function renderOrderItemsSummary() {
    const itemsWrap = document.getElementById("checkoutItemsSummary");
    const subtotalEl = document.getElementById("checkoutSubtotal");
    const shippingEl = document.getElementById("checkoutShipping");
    const totalEl = document.getElementById("checkoutTotal");

    if (!itemsWrap || !subtotalEl || !totalEl) return;

    if (cart.length === 0) {
      window.location.href = "cart.html";
      return;
    }

    itemsWrap.innerHTML = cart.map(function (item) {
      let imgPath = item.image;
      if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
        imgPath = "../../" + imgPath;
      }
      return `
        <div style="display:flex; align-items:center; gap:1em; margin-bottom:.8em;">
          <div style="width:48px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
            ${imgPath ? '<img src="' + imgPath + '" style="width:100%; height:100%; object-fit:cover;">' : ''}
          </div>
          <div style="flex:1;">
            <p style="margin:0; font-size:.88rem; font-weight:600;">${window.Formatters.escapeHTML(item.name)}</p>
            <p style="margin:0; font-size:.76rem; color:var(--ink-soft);">Size: ${item.size || 'M'}</p>
          </div>
          <span style="font-size:.88rem; font-weight:600;">${window.Formatters.formatINR(item.price * item.qty)}</span>
        </div>
      `;
    }).join("");

    const subtotal = cart.reduce(function (sum, item) { return sum + item.price * item.qty; }, 0);
    const grandTotal = subtotal + selectedShippingFee;

    subtotalEl.textContent = window.Formatters.formatINR(subtotal);
    if (shippingEl) {
      shippingEl.textContent = selectedShippingFee === 0 ? "FREE" : window.Formatters.formatINR(selectedShippingFee);
    }
    totalEl.textContent = window.Formatters.formatINR(grandTotal);
  }

  function renderAddresses() {
    const wrap = document.getElementById("addressCardsWrap");
    if (!wrap) return;

    wrap.innerHTML = addresses.map(function (addr) {
      const isSelected = addr.id === selectedAddressId;
      return `
        <label class="address-card ${isSelected ? 'selected' : ''}" data-addr-id="${addr.id}">
          <input type="radio" name="addressSelection" value="${addr.id}" ${isSelected ? 'checked' : ''}>
          <div class="address-details">
            <h4>${window.Formatters.escapeHTML(addr.name)} — ${window.Formatters.escapeHTML(addr.recipient)}</h4>
            <p>${window.Formatters.escapeHTML(addr.street)}, ${window.Formatters.escapeHTML(addr.city)}, ${window.Formatters.escapeHTML(addr.state)} - ${window.Formatters.escapeHTML(addr.pincode)}</p>
            <p style="margin-top:.2em; font-size:.78rem; color:var(--ink-soft);">Mobile: +91 ${window.Formatters.escapeHTML(addr.phone)}</p>
          </div>
        </label>
      `;
    }).join("");

    wrap.querySelectorAll('input[name="addressSelection"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        selectedAddressId = radio.value;
        renderAddresses();
      });
    });
  }

  function saveCheckoutInfoAndProceed() {
    const selectedAddr = addresses.find(function (a) { return a.id === selectedAddressId; });
    const emailInput = document.getElementById("contactEmail");
    const nameInput = document.getElementById("contactName");
    const phoneInput = document.getElementById("contactPhone");

    const contactEmail = emailInput ? emailInput.value.trim() : (currentUser ? currentUser.email : "customer@example.com");
    const contactName = nameInput ? nameInput.value.trim() : (currentUser ? currentUser.name : "Customer");
    const contactPhone = phoneInput ? phoneInput.value.trim() : "9876543210";

    if (!selectedAddr) {
      if (window.Toast) window.Toast.show("Please select a delivery address");
      return;
    }

    const subtotal = cart.reduce(function (sum, item) { return sum + item.price * item.qty; }, 0);
    const grandTotal = subtotal + selectedShippingFee;

    const checkoutInfo = {
      contact: {
        name: contactName,
        email: contactEmail,
        phone: contactPhone
      },
      address: selectedAddr,
      shippingFee: selectedShippingFee,
      subtotal: subtotal,
      grandTotal: grandTotal,
      items: cart
    };

    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(CHECKOUT_INFO_KEY, checkoutInfo);
    }

    window.location.href = "payment.html";
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!currentUser) {
      window.location.href = "../auth/login.html";
      return;
    }
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    renderOrderItemsSummary();
    renderAddresses();

    // Auto-fill user contact fields
    if (currentUser) {
      const emailInput = document.getElementById("contactEmail");
      const nameInput = document.getElementById("contactName");
      const phoneInput = document.getElementById("contactPhone");
      if (emailInput && currentUser.email) emailInput.value = currentUser.email;
      if (nameInput && currentUser.name) nameInput.value = currentUser.name;
      if (phoneInput && currentUser.phone) phoneInput.value = currentUser.phone;
    }

    // Toggle Add New Address form
    const toggleBtn = document.getElementById("toggleAddAddressBtn");
    const newAddressBox = document.getElementById("newAddressBox");
    if (toggleBtn && newAddressBox) {
      toggleBtn.addEventListener("click", function () {
        newAddressBox.classList.toggle("hidden");
      });
    }

    // Save New Address Form submit
    const saveAddrBtn = document.getElementById("saveNewAddressBtn");
    if (saveAddrBtn) {
      saveAddrBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const street = document.getElementById("newStreet").value.trim();
        const city = document.getElementById("newCity").value.trim();
        const state = document.getElementById("newState").value.trim();
        const pincode = document.getElementById("newPincode").value.trim();
        const recipient = document.getElementById("newRecipient").value.trim();

        if (!street || !city || !state || !pincode) {
          if (window.Toast) window.Toast.show("Please fill out required address fields");
          return;
        }

        const newAddr = {
          id: window.Helpers ? window.Helpers.uid("addr") : "addr_" + Date.now(),
          name: "New Address",
          recipient: recipient || (currentUser ? currentUser.name : "Customer"),
          phone: currentUser ? currentUser.phone : "9876543210",
          street: street,
          city: city,
          state: state,
          pincode: pincode
        };

        addresses.push(newAddr);
        selectedAddressId = newAddr.id;
        renderAddresses();
        newAddressBox.classList.add("hidden");
        if (window.Toast) window.Toast.show("Address added!");
      });
    }

    // Shipping options selection
    document.querySelectorAll('input[name="deliveryOption"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        selectedShippingFee = radio.value === "express" ? 150 : 0;
        renderOrderItemsSummary();
      });
    });

    // Continue to Payment button
    const btnProceed = document.getElementById("proceedToPaymentBtn");
    if (btnProceed) {
      btnProceed.addEventListener("click", saveCheckoutInfoAndProceed);
    }
  });
})();
