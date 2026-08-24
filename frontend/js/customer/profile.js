/* =========================================================
   LIKSHORA — Customer Profile Controller
   User info sync, personal info updates, address CRUD, order history,
   review submissions & session logout
   ========================================================= */

(function() {
  const CURRENT_USER_KEY = "rv_current_user";
  const ADDRESSES_KEY = "rv_addresses";
  const ORDERS_KEY = "rv_orders";
  const REVIEWS_KEY = "rv_reviews";
  const WISHLIST_KEY = "rv_wishlist";

  let currentUser = window.StorageUtils ? window.StorageUtils.readJSON(CURRENT_USER_KEY, null) : null;
  let addresses = window.StorageUtils ? window.StorageUtils.readJSON(ADDRESSES_KEY, []) : [];
  let orders = window.StorageUtils ? window.StorageUtils.readJSON(ORDERS_KEY, []) : [];
  let reviews = window.StorageUtils ? window.StorageUtils.readJSON(REVIEWS_KEY, []) : [];

  function syncProfileSidebar() {
    if (!currentUser) return;
    const avatarEl = document.getElementById("sidebarInitials") || document.getElementById("profileAvatar");
    const nameEl = document.getElementById("sidebarName") || document.getElementById("profileSidebarName");
    const emailEl = document.getElementById("sidebarEmail") || document.getElementById("profileSidebarEmail");

    const initials = window.Formatters ? window.Formatters.getInitials(currentUser.name || "Customer") : "C";

    if (nameEl) nameEl.textContent = currentUser.name || "Customer";
    if (emailEl) emailEl.textContent = currentUser.email || "customer@example.com";
    if (avatarEl) avatarEl.textContent = initials;
  }

  function initPersonalInformationPage() {
    const form = document.getElementById("personalInfoForm");
    if (!form) return;

    const firstNameInput = document.getElementById("infoFirstName");
    const lastNameInput = document.getElementById("infoLastName");
    const emailInput = document.getElementById("infoEmail");
    const phoneInput = document.getElementById("infoPhone");

    if (currentUser) {
      const nameParts = (currentUser.name || "").split(" ");
      if (firstNameInput) firstNameInput.value = nameParts[0] || "";
      if (lastNameInput) lastNameInput.value = nameParts.slice(1).join(" ") || "";
      if (emailInput) emailInput.value = currentUser.email || "";
      if (phoneInput) phoneInput.value = currentUser.phone || "";
    }

    form.addEventListener("submit", function(e) {
      e.preventDefault();

      const fn = firstNameInput ? firstNameInput.value.trim() : "";
      const ln = lastNameInput ? lastNameInput.value.trim() : "";
      const email = emailInput ? emailInput.value.trim() : "";
      const phone = phoneInput ? phoneInput.value.trim() : "";

      if (!fn || !email || !phone) {
        if (window.Toast) window.Toast.show("Please fill out required fields.");
        return;
      }

      currentUser.name = (fn + (ln ? " " + ln : "")).trim();
      currentUser.email = email;
      currentUser.phone = phone;

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(CURRENT_USER_KEY, currentUser);
        const registered = window.StorageUtils.readJSON("rv_registered_users", []);
        const idx = registered.findIndex(function(u) { return u.id === currentUser.id || u.email === currentUser.email; });
        if (idx !== -1) {
          registered[idx] = Object.assign({}, registered[idx], currentUser);
          window.StorageUtils.writeJSON("rv_registered_users", registered);
        }
      }

      syncProfileSidebar();
      if (window.NavbarComponent) {
        window.NavbarComponent.updateUserAvatar(currentUser);
      }

      if (window.Toast) window.Toast.show("Personal information updated successfully!");
    });
  }

  function renderAddressesPage() {
    const grid = document.getElementById("addressGrid") || document.getElementById("addressesGrid");
    if (!grid) return;

    if (!addresses || addresses.length === 0) {
      grid.innerHTML = `<p style="grid-column:1/-1; color:var(--ink-soft); font-size:.9rem;">No saved addresses found. Add a new delivery destination below.</p>`;
      return;
    }

    grid.innerHTML = addresses.map(function(addr) {
      const fullStreet = addr.street + (addr.flat ? ", " + addr.flat : "");
      return `
        <div class="address-box ${addr.isDefault ? 'default-address' : ''}" style="border:1px solid var(--stone); border-radius:var(--radius-sm); padding:1.2em; background:var(--white);">
          ${addr.isDefault ? '<span class="default-badge" style="background:var(--gold); color:var(--white); font-size:.72rem; padding:.2em .6em; border-radius:var(--radius-xs); text-transform:uppercase; font-weight:600;">Default</span>' : ''}
          <div style="margin-top:.4em;">
            <h4 style="margin:0 0 .3em; font-size:1rem; font-family:var(--font-display);">${window.Formatters ? window.Formatters.escapeHTML(addr.name || 'Address') : addr.name} — ${window.Formatters ? window.Formatters.escapeHTML(addr.recipient || currentUser.name) : addr.recipient}</h4>
            <p style="margin:0; font-size:.86rem; color:var(--ink-soft); line-height:1.45;">
              ${window.Formatters ? window.Formatters.escapeHTML(fullStreet) : fullStreet}, ${window.Formatters ? window.Formatters.escapeHTML(addr.city) : addr.city}, ${window.Formatters ? window.Formatters.escapeHTML(addr.state) : addr.state} - ${window.Formatters ? window.Formatters.escapeHTML(addr.pincode) : addr.pincode}
            </p>
            <p style="margin-top:.3em; font-size:.78rem; color:var(--stone);">Mobile: +91 ${window.Formatters ? window.Formatters.escapeHTML(addr.phone || currentUser.phone) : addr.phone}</p>
          </div>
          <div style="display:flex; gap:.6em; margin-top:.8em;">
            ${!addr.isDefault ? '<button class="btn btn-outline" style="padding:.3em .7em; font-size:.78rem;" data-set-default="' + addr.id + '">Set Default</button>' : ''}
            <button class="btn btn-outline" style="padding:.3em .7em; font-size:.78rem; color:var(--rust); border-color:var(--stone);" data-delete-addr="${addr.id}">Delete</button>
          </div>
        </div>
      `;
    }).join("");
  }

  function initAddressesPage() {
    renderAddressesPage();

    const grid = document.getElementById("addressGrid") || document.getElementById("addressesGrid");
    if (grid) {
      grid.addEventListener("click", function(e) {
        const defaultBtn = e.target.closest("[data-set-default]");
        const deleteBtn = e.target.closest("[data-delete-addr]");

        if (defaultBtn) {
          const id = defaultBtn.dataset.setDefault;
          addresses.forEach(function(a) { a.isDefault = (a.id === id); });
          if (window.StorageUtils) window.StorageUtils.writeJSON(ADDRESSES_KEY, addresses);
          renderAddressesPage();
          if (window.Toast) window.Toast.show("Default address updated!");
        }

        if (deleteBtn) {
          const id = deleteBtn.dataset.deleteAddr;
          addresses = addresses.filter(function(a) { return a.id !== id; });
          if (window.StorageUtils) window.StorageUtils.writeJSON(ADDRESSES_KEY, addresses);
          renderAddressesPage();
          if (window.Toast) window.Toast.show("Address deleted");
        }
      });
    }

    const addBtn = document.getElementById("addAddressBtn") || document.getElementById("addAddressModalBtn");
    const modalId = document.getElementById("addressModalOverlay") ? "addressModalOverlay" : "addAddressModal";

    if (addBtn) {
      addBtn.addEventListener("click", function() {
        if (window.Modal) window.Modal.open(modalId);
      });
    }

    const closeBtn = document.getElementById("addressModalClose");
    if (closeBtn) {
      closeBtn.addEventListener("click", function() {
        if (window.Modal) window.Modal.close(modalId);
      });
    }

    const form = document.getElementById("addressForm");
    const saveBtn = document.getElementById("saveAddressModalBtn");

    function saveAddress(e) {
      if (e) e.preventDefault();

      const label = (document.getElementById("addrLabel") || document.getElementById("modalAddrTitle")).value.trim() || "Saved Address";
      const recipient = (document.getElementById("addrName") || document.getElementById("modalAddrRecipient")).value.trim() || currentUser.name;
      const phone = (document.getElementById("addrPhone") || document.getElementById("modalAddrPhone")).value.trim() || currentUser.phone;
      const flat = document.getElementById("addrFlat") ? document.getElementById("addrFlat").value.trim() : "";
      const street = (document.getElementById("addrStreet") || document.getElementById("modalAddrStreet")).value.trim();
      const city = (document.getElementById("addrCity") || document.getElementById("modalAddrCity")).value.trim();
      const state = (document.getElementById("addrState") || document.getElementById("modalAddrState")).value.trim();
      const pincode = (document.getElementById("addrPincode") || document.getElementById("modalAddrPincode")).value.trim();
      const isDefaultCheckbox = document.getElementById("addrDefault");
      const setAsDefault = isDefaultCheckbox ? isDefaultCheckbox.checked : (addresses.length === 0);

      if (!street || !city || !state || !pincode) {
        if (window.Toast) window.Toast.show("Please fill out all required address fields.");
        return;
      }

      if (setAsDefault) {
        addresses.forEach(function(a) { a.isDefault = false; });
      }

      const newAddr = {
        id: "addr_" + Date.now(),
        name: label,
        recipient: recipient,
        phone: phone,
        flat: flat,
        street: street,
        city: city,
        state: state,
        pincode: pincode,
        isDefault: setAsDefault || addresses.length === 0
      };

      addresses.push(newAddr);
      if (window.StorageUtils) window.StorageUtils.writeJSON(ADDRESSES_KEY, addresses);
      renderAddressesPage();
      if (window.Modal) window.Modal.close(modalId);
      if (window.Toast) window.Toast.show("Address saved successfully!");
    }

    if (form) {
      form.addEventListener("submit", saveAddress);
    } else if (saveBtn) {
      saveBtn.addEventListener("click", saveAddress);
    }
  }

  function renderOrdersPage() {
    const listWrap = document.getElementById("ordersContainer") || document.getElementById("ordersListWrap");
    const emptyNotice = document.getElementById("emptyOrdersState");

    if (!listWrap) return;

    if (!orders || orders.length === 0) {
      if (emptyNotice) {
        emptyNotice.classList.remove("hidden");
        listWrap.innerHTML = "";
      } else {
        listWrap.innerHTML = `
          <div class="empty-cart-state" style="padding:2em 0; text-align:center;">
            <div class="empty-cart-icon"></div>
            <h2 class="empty-cart-title">No orders placed yet</h2>
            <p class="empty-cart-text">Explore our collection of handpicked kurtas to place your first order.</p>
            <a href="../customer/products.html" class="btn btn-primary" style="margin-top:1em; display:inline-block;">Browse Catalog</a>
          </div>
        `;
      }
      return;
    }

    if (emptyNotice) {
      emptyNotice.classList.add("hidden");
    }

    listWrap.innerHTML = orders.map(function(order) {
      const itemsList = (order.items || []).map(function(item) {
        return `${window.Formatters ? window.Formatters.escapeHTML(item.name) : item.name} (x${item.qty})`;
      }).join(", ");

      const totalVal = window.Formatters ? window.Formatters.formatINR(order.grandTotal) : "₹" + order.grandTotal;

      return `
        <div class="checkout-section-box" style="margin-bottom:1.2em; border:1px solid var(--stone); border-radius:var(--radius-sm); padding:1.2em; background:var(--white);">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--sand-deep); padding-bottom:.8em; margin-bottom:.8em; flex-wrap:wrap; gap:.5em;">
            <div>
              <h4 style="margin:0; font-size:1.05rem; font-family:var(--font-display);">Order #${window.Formatters ? window.Formatters.escapeHTML(order.orderNumber) : order.orderNumber}</h4>
              <span style="font-size:.78rem; color:var(--ink-soft);">${order.date || 'Recent'}</span>
            </div>
            <div>
              <span class="tracking-status-badge" style="background:var(--sand-deep); padding:.2em .6em; font-size:.78rem; border-radius:var(--radius-xs); font-weight:600;">${order.status || 'Paid & Confirmed'}</span>
              <span style="font-family:var(--font-display); font-size:1.1rem; color:var(--gold); margin-left:.6em;">${totalVal}</span>
            </div>
          </div>
          <p style="font-size:.88rem; color:var(--ink-soft); margin:0 0 1em;"><strong>Items:</strong> ${itemsList}</p>
          <div style="display:flex; gap:1em;">
            <a href="../customer/order-tracking.html?order=${order.orderNumber}" class="btn btn-outline" style="padding:.4em 1em; font-size:.82rem;">Track Package &rarr;</a>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderReviewsPage() {
    const listWrap = document.getElementById("reviewsContainer") || document.getElementById("reviewsListWrap");
    if (!listWrap) return;

    if (!reviews || reviews.length === 0) {
      listWrap.innerHTML = `<p style="color:var(--ink-soft); font-size:.9rem;">No reviews submitted yet.</p>`;
      return;
    }

    listWrap.innerHTML = reviews.map(function(r) {
      const stars = "★".repeat(r.rating || 5);
      const title = r.title ? `<h5 style="margin:.3em 0; font-size:.92rem;">${window.Formatters ? window.Formatters.escapeHTML(r.title) : r.title}</h5>` : '';
      return `
        <div class="user-review-card" style="border:1px solid var(--stone); border-radius:var(--radius-sm); padding:1.2em; background:var(--white); margin-bottom:1em;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 class="review-product-title" style="margin:0; font-size:1rem; font-family:var(--font-display);">${window.Formatters ? window.Formatters.escapeHTML(r.productName) : r.productName}</h4>
            <span style="font-size:.76rem; color:var(--stone);">${r.date}</span>
          </div>
          <div class="rating-stars" style="color:var(--gold); font-size:1rem; margin:.3em 0;">${stars}</div>
          ${title}
          <p class="review-body" style="margin:0; font-size:.88rem; color:var(--ink-soft); line-height:1.45;">${window.Formatters ? window.Formatters.escapeHTML(r.comment) : r.comment}</p>
        </div>
      `;
    }).join("");
  }

  function initReviewsPage() {
    renderReviewsPage();

    const form = document.getElementById("reviewForm");
    const writeBtn = document.getElementById("writeReviewModalBtn");
    const saveBtn = document.getElementById("saveReviewModalBtn");

    if (writeBtn) writeBtn.addEventListener("click", function() { if (window.Modal) window.Modal.open("addReviewModal"); });

    function submitReview(e) {
      if (e) e.preventDefault();

      const prodSelect = document.getElementById("reviewProduct") || document.getElementById("modalReviewProduct");
      const ratingSelect = document.getElementById("reviewRating") || document.getElementById("modalReviewRating");
      const titleInput = document.getElementById("reviewTitle");
      const commentInput = document.getElementById("reviewComment") || document.getElementById("modalReviewComment");

      const prodName = prodSelect ? prodSelect.value : "Kurta Set";
      const rating = ratingSelect ? parseInt(ratingSelect.value, 10) : 5;
      const title = titleInput ? titleInput.value.trim() : "";
      const comment = commentInput ? commentInput.value.trim() : "";

      if (!comment) {
        if (window.Toast) window.Toast.show("Please enter your review details.");
        return;
      }

      const newReview = {
        id: "rev_" + Date.now(),
        productName: prodName,
        rating: rating || 5,
        title: title,
        date: "Today",
        comment: comment
      };

      reviews.unshift(newReview);
      if (window.StorageUtils) window.StorageUtils.writeJSON(REVIEWS_KEY, reviews);
      renderReviewsPage();
      if (window.Modal) window.Modal.close("addReviewModal");
      if (window.Toast) window.Toast.show("Thank you for your feedback!");

      if (form) form.reset();
    }

    if (form) {
      form.addEventListener("submit", submitReview);
    } else if (saveBtn) {
      saveBtn.addEventListener("click", submitReview);
    }
  }

  function updateOverviewStats() {
    const statOrders = document.getElementById("statOrdersCount");
    const statWishlist = document.getElementById("statWishlistCount");
    const statCart = document.getElementById("statCartCount");
    const statAddresses = document.getElementById("statAddressesCount");

    const wishlist = window.StorageUtils ? window.StorageUtils.readJSON(WISHLIST_KEY, []) : [];
    const cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];

    if (statOrders) statOrders.textContent = orders.length;
    if (statWishlist) statWishlist.textContent = wishlist.length;
    if (statCart) statCart.textContent = cart.length;
    if (statAddresses) statAddresses.textContent = addresses.length;
  }

  function checkAuthProtection() {
    if (!currentUser && window.location.pathname.includes("/pages/profile/")) {
      window.location.href = "../auth/login.html";
      return false;
    }
    return true;
  }

  function initLogout() {
    const logoutBtns = document.querySelectorAll(".logout-trigger, .logout-btn-trigger, .logout-link, #signOutBtn");
    logoutBtns.forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        e.preventDefault();
        if (window.StorageUtils) {
          window.StorageUtils.writeJSON(CURRENT_USER_KEY, null);
          const CONFIG_USER_KEY = (window.RV_CONFIG && window.RV_CONFIG.STORAGE_KEYS && window.RV_CONFIG.STORAGE_KEYS.USER) || "rv_current_user";
          window.StorageUtils.writeJSON(CONFIG_USER_KEY, null);
          window.StorageUtils.writeJSON("rv_cart", []);
        }
        if (window.NavbarComponent && window.NavbarComponent.updateCartBadge) {
          window.NavbarComponent.updateCartBadge(0);
        }
        if (window.Toast) window.Toast.show("Logged out successfully.");
        setTimeout(function() {
          if (window.location.pathname.includes("/pages/profile/") || window.location.pathname.includes("/pages/customer/")) {
            window.location.href = "../../index.html";
          } else {
            window.location.href = "index.html";
          }
        }, 500);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (!checkAuthProtection()) return;
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    syncProfileSidebar();
    updateOverviewStats();
    initPersonalInformationPage();
    initAddressesPage();
    renderOrdersPage();
    initReviewsPage();
    initLogout();
  });
})();

