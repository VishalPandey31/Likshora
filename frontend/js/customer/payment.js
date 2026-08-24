/* =========================================================
   LIKSHORA — Payment Adapter Simulation Controller
   Isolated payment simulation layer for Cards, UPI, QR & COD.
   Easily swappable with real payment APIs (e.g. Razorpay/Stripe) later.
   ========================================================= */

// Cleanly isolated Payment Simulation Provider Layer
window.PaymentProviderSimulation = (function() {
  return {
    processPayment: function(paymentDetails, callback) {
      console.log("[PaymentProviderSimulation] Processing frontend simulation payment:", paymentDetails);

      // Simulate network response latency
      setTimeout(function() {
        callback({
          success: true,
          transactionId: "TXN_" + Date.now().toString(36).toUpperCase() + Math.random().toString(36).slice(2, 6).toUpperCase(),
          method: paymentDetails.methodLabel || paymentDetails.method,
          status: "Paid & Confirmed",
          timestamp: new Date().toISOString()
        });
      }, 1200);
    }
  };
})();

(function() {
  const CHECKOUT_INFO_KEY = "rv_checkout_info";
  const CART_KEY = "rv_cart";
  const LAST_ORDER_KEY = "rv_last_order";
  const ORDERS_KEY = "rv_orders";

  let checkoutInfo = window.StorageUtils ? window.StorageUtils.readJSON(CHECKOUT_INFO_KEY, null) : null;
  let selectedMethod = "razorpay";

  const DEFAULT_CATALOG = [
    { id: "AK01", sku: "AK01-RUST", name: "Rust Bell-Sleeve Printed Kurti", price: 2299, was: 2799, category: "kurtis", stock: 3, rating: 4.8, status: "Active", description: "Breathable 100% cotton printed kurti with bell sleeves.", image: "../../assets/images/products/product-kurti-1.jpg" }
  ];

  function renderPaymentSummary() {
    if (!checkoutInfo || !checkoutInfo.items || checkoutInfo.items.length === 0) {
      const buyNowItem = window.StorageUtils ? window.StorageUtils.readJSON("rv_buy_now_item", null) : null;
      if (buyNowItem) {
        checkoutInfo = {
          contact: { name: "Customer", email: "customer@example.com", phone: "9876543210" },
          address: { recipient: "Valued Customer", street: "Flat 402, Lotus Apartments, MG Road", city: "Bengaluru", state: "Karnataka", pincode: "560001" },
          shippingFee: 0,
          subtotal: buyNowItem.price * (buyNowItem.qty || 1),
          grandTotal: buyNowItem.price * (buyNowItem.qty || 1),
          items: [buyNowItem]
        };
      } else {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("buy_now") === "true") {
          const buyId = urlParams.get("id");
          const buySize = urlParams.get("size") || "M";
          const buyQty = parseInt(urlParams.get("qty") || "1", 10);
          const storedProducts = window.StorageUtils ? window.StorageUtils.readJSON("rv_products", DEFAULT_CATALOG) : DEFAULT_CATALOG;
          const products = (storedProducts && storedProducts.length) ? storedProducts : DEFAULT_CATALOG;
          const found = products.find(function(p) { return p.id === buyId; }) || DEFAULT_CATALOG[0];
          if (found) {
            const item = Object.assign({}, found, { size: buySize, qty: buyQty });
            checkoutInfo = {
              contact: { name: "Customer", email: "customer@example.com", phone: "9876543210" },
              address: { recipient: "Valued Customer", street: "Flat 402, Lotus Apartments, MG Road", city: "Bengaluru", state: "Karnataka", pincode: "560001" },
              shippingFee: 0,
              subtotal: item.price * item.qty,
              grandTotal: item.price * item.qty,
              items: [item]
            };
          }
        }
      }
    }

    if (!checkoutInfo || !checkoutInfo.items || checkoutInfo.items.length === 0) {
      window.location.href = "cart.html";
      return;
    }

    const totalEl = document.getElementById("paymentGrandTotal");
    const addrSummaryEl = document.getElementById("paymentAddressSummary");

    if (totalEl) {
      totalEl.textContent = window.Formatters.formatINR(checkoutInfo.grandTotal);
    }

    if (addrSummaryEl && checkoutInfo.address) {
      const a = checkoutInfo.address;
      addrSummaryEl.innerHTML = `
        <strong>Delivering to:</strong> ${window.Formatters.escapeHTML(a.recipient)}<br>
        ${window.Formatters.escapeHTML(a.street)}, ${window.Formatters.escapeHTML(a.city)}, ${window.Formatters.escapeHTML(a.state)} - ${window.Formatters.escapeHTML(a.pincode)}
      `;
    }
  }

  function initCardPreview() {
    const cardNumberInput = document.getElementById("cardNumberInput");
    const cardExpiryInput = document.getElementById("cardExpiryInput");
    const cardNameInput = document.getElementById("cardNameInput");
    const previewNumber = document.getElementById("previewNumber");
    const previewName = document.getElementById("previewName");
    const previewExpiry = document.getElementById("previewExpiry");

    if (cardNumberInput) {
      cardNumberInput.addEventListener("input", function() {
        const digits = cardNumberInput.value.replace(/\D/g, "").slice(0, 16);
        cardNumberInput.value = digits.replace(/(.{4})/g, "$1 ").trim();

        const groups = digits.match(/.{1,4}/g) || [];
        const previewGroups = [0, 1, 2, 3].map(function(i) {
          return groups[i] ? groups[i].padEnd(4, "•") : "••••";
        });
        if (previewNumber) previewNumber.textContent = previewGroups.join(" ");
      });
    }

    if (cardNameInput) {
      cardNameInput.addEventListener("input", function() {
        if (previewName) previewName.textContent = cardNameInput.value.trim().toUpperCase() || "YOUR NAME";
      });
    }

    if (cardExpiryInput) {
      cardExpiryInput.addEventListener("input", function() {
        let digits = cardExpiryInput.value.replace(/\D/g, "").slice(0, 4);
        if (digits.length >= 3) digits = digits.slice(0, 2) + "/" + digits.slice(2);
        cardExpiryInput.value = digits;
        if (previewExpiry) previewExpiry.textContent = digits || "MM/YY";
      });
    }
  }

  async function handlePaymentSubmit() {
    const payBtn = document.getElementById("payNowBtn");
    if (payBtn) {
      payBtn.disabled = true;
      payBtn.textContent = "Processing Order...";
    }

    // 1. Create order on backend REST API
    const orderPayload = {
      payment_method: selectedMethod,
      shipping_address: checkoutInfo ? checkoutInfo.address : null,
      shipping_address_id: checkoutInfo && checkoutInfo.address ? checkoutInfo.address.id : null,
      items: checkoutInfo && checkoutInfo.items ? checkoutInfo.items.map(i => ({
        product_id: i.product_id || i.id,
        quantity: i.qty || i.quantity || 1,
        size: i.size || "M"
      })) : []
    };

    let orderRes = null;
    try {
      if (window.OrderAPI && window.OrderAPI.createOrder) {
        orderRes = await window.OrderAPI.createOrder(orderPayload);
      }
    } catch (e) {
      console.warn("Backend order creation error:", e);
    }

    const orderData = (orderRes && orderRes.success && orderRes.data) ? orderRes.data : null;
    const orderId = orderData ? (orderData.id || orderData.order_id || orderData.order_number || orderData.orderNumber) : ("ORD_" + Date.now());
    const payableAmount = orderData ? (orderData.payable_amount || orderData.grand_total || (checkoutInfo ? checkoutInfo.grandTotal : 0)) : (checkoutInfo ? checkoutInfo.grandTotal : 0);

    // Save temporary order context for success page
    const lastOrderRecord = {
      orderNumber: orderId,
      date: new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }),
      contact: checkoutInfo ? checkoutInfo.contact : null,
      address: checkoutInfo ? checkoutInfo.address : null,
      items: checkoutInfo ? checkoutInfo.items : [],
      grandTotal: payableAmount,
      paymentMethod: selectedMethod === "cod" ? "Cash on Delivery (COD)" : "Pay with Razorpay",
      status: selectedMethod === "cod" ? "Confirmed (COD)" : "Paid & Confirmed"
    };

    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(LAST_ORDER_KEY, lastOrderRecord);
    }

    // 2. COD Flow
    if (selectedMethod === "cod") {
      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(CART_KEY, []);
        window.StorageUtils.remove("rv_buy_now_item");
        window.StorageUtils.remove("rv_checkout_info");
      }
      if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(0);
      if (window.Toast) window.Toast.show("Order placed successfully!");
      window.location.href = "order-success.html";
      return;
    }

    // 3. Razorpay Payment Gateway Flow
    if (selectedMethod === "razorpay") {
      try {
        let rzpOrderRes = await window.PaymentAPI.createRazorpayOrder(orderId);
        if (!rzpOrderRes || !rzpOrderRes.success || !rzpOrderRes.data) {
          const errorMsg = (rzpOrderRes && (rzpOrderRes.error || rzpOrderRes.message)) || "Failed to create Razorpay Order on server";
          alert("Payment Initialization Failed: " + errorMsg);
          if (payBtn) { payBtn.disabled = false; payBtn.textContent = "Pay & Complete Order →"; }
          return;
        }

        const rzpData = rzpOrderRes.data;
        const rzpOrderId = rzpData.razorpay_order_id || rzpData.id;
        const razorpayKeyId = rzpData.key_id || rzpData.razorpay_key_id || (window.RV_CONFIG && window.RV_CONFIG.RAZORPAY_KEY_ID);
        const amountInPaise = rzpData.amount;
        const currency = rzpData.currency || "INR";

        const options = {
          key: razorpayKeyId,
          amount: amountInPaise,
          currency: currency,
          name: "Likshora",
          description: "Order #" + (rzpData.order_number || orderId),
          image: "../../assets/images/website/logo-icon.png",
          order_id: rzpOrderId,
          prefill: {
            name: checkoutInfo && checkoutInfo.contact ? checkoutInfo.contact.name : "Customer",
            email: checkoutInfo && checkoutInfo.contact ? checkoutInfo.contact.email : "customer@example.com",
            contact: checkoutInfo && checkoutInfo.contact ? checkoutInfo.contact.phone : "9876543210"
          },
          theme: { color: "#340B10" },
          handler: async function(response) {
            // Show verification screen
            const verifyOverlay = document.getElementById("paymentVerifyOverlay");
            const verifyState = document.getElementById("paymentVerifyingState");
            const successState = document.getElementById("paymentSuccessState");
            if (verifyOverlay) verifyOverlay.classList.add("open");
            if (verifyState) verifyState.classList.remove("hidden");

            // Verify payment on backend REST API
            const verifyRes = await window.PaymentAPI.verifyRazorpayPayment(response, orderId);

            if (verifyRes.success) {
              if (verifyState) verifyState.classList.add("hidden");
              if (successState) successState.classList.remove("hidden");

              if (window.StorageUtils) {
                window.StorageUtils.writeJSON(CART_KEY, []);
                window.StorageUtils.remove("rv_buy_now_item");
                window.StorageUtils.remove("rv_checkout_info");
              }
              if (window.NavbarComponent) window.NavbarComponent.updateCartBadge(0);

              setTimeout(function() {
                window.location.href = "order-success.html";
              }, 1000);
            } else {
              if (verifyOverlay) verifyOverlay.classList.remove("open");
              alert("Payment verification failed: " + (verifyRes.error || "Invalid signature"));
              if (payBtn) { payBtn.disabled = false; payBtn.textContent = "Pay & Complete Order →"; }
            }
          },
          modal: {
            ondismiss: function() {
              if (payBtn) { payBtn.disabled = false; payBtn.textContent = "Pay & Complete Order →"; }
            }
          }
        };

        if (typeof window.Razorpay !== "undefined") {
          const rzp = new window.Razorpay(options);
          rzp.open();
        } else {
          // Alert user if Razorpay SDK script is blocked or offline
          console.warn("Razorpay SDK not loaded in browser environment");
          alert("Razorpay payment gateway script was not loaded. Please check your internet connection.");
          if (payBtn) { payBtn.disabled = false; payBtn.textContent = "Pay & Complete Order →"; }
        }
      } catch (err) {
        console.error("Razorpay initiation error:", err);
        alert("Payment initialization failed. Please try again.");
        if (payBtn) { payBtn.disabled = false; payBtn.textContent = "Pay & Complete Order →"; }
      }
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    if (window.NavbarComponent) window.NavbarComponent.init();
    if (window.FooterComponent) window.FooterComponent.init();

    renderPaymentSummary();
    initCardPreview();

    // Payment method selector change
    document.querySelectorAll('input[name="paymentMethod"]').forEach(function(radio) {
      radio.addEventListener("change", function() {
        selectedMethod = radio.value;
        document.querySelectorAll(".payment-option-fields").forEach(function(panel) {
          panel.hidden = panel.dataset.for !== selectedMethod;
        });
        document.querySelectorAll(".payment-option").forEach(function(opt) {
          opt.classList.remove("is-selected");
        });
        radio.closest(".payment-option").classList.add("is-selected");
      });
    });

    const preselected = document.querySelector('input[name="paymentMethod"]:checked');
    if (preselected) preselected.closest(".payment-option").classList.add("is-selected");

    const payBtn = document.getElementById("payNowBtn");
    if (payBtn) {
      payBtn.addEventListener("click", handlePaymentSubmit);
    }
  });
})();
