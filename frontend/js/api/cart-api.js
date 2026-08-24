/* =========================================================
   LIKSHORA — Shopping Bag Cart API Abstraction
   Placeholder interfaces for cart item additions, quantity & state
   ========================================================= */

window.CartAPI = (function() {
  const CART_KEY = "rv_cart";
  const TOKEN_KEY = "rv_access_token";

  function isAuthenticated() {
    return !!localStorage.getItem(TOKEN_KEY);
  }

  return {
    getCart: async function() {
      if (!isAuthenticated()) {
        const localCart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];
        const total = localCart.reduce((sum, i) => sum + (parseFloat(i.price || 0) * (i.qty || i.quantity || 1)), 0);
        return window.APIClient.response(true, { items: localCart, subtotal: total, grandTotal: total }, null, 200);
      }

      const res = await window.APIClient.get("/cart");
      if (res.success && res.data) {
        const cartData = res.data;
        const items = cartData.items || cartData.cart_items || [];
        const subtotal = cartData.subtotal !== undefined ? cartData.subtotal : items.reduce((s, i) => s + (parseFloat(i.price || (i.product ? i.product.selling_price : 0)) * i.quantity), 0);
        return window.APIClient.response(true, { items: items, subtotal: subtotal, grandTotal: subtotal }, null, res.status);
      }
      return res;
    },

    addToCart: async function(item) {
      if (!isAuthenticated()) {
        return window.APIClient.response(false, { redirect: "login" }, "Please log in to add items to your shopping bag", 401);
      }

      const payload = {
        product_id: item.product_id || item.id,
        quantity: item.quantity || item.qty || 1,
        size: item.size || null,
        color: item.color || null
      };

      const res = await window.APIClient.post("/cart", payload);
      if (res.success) {
        return await this.getCart();
      }
      return res;
    },

    updateQuantity: async function(cartItemIdOrProductId, quantity) {
      if (!isAuthenticated()) {
        return window.APIClient.response(false, null, "Please log in", 401);
      }

      const res = await window.APIClient.put(`/cart/${cartItemIdOrProductId}`, { quantity: Math.max(1, quantity) });
      if (res.success) {
        return await this.getCart();
      }
      return res;
    },

    removeFromCart: async function(cartItemIdOrProductId) {
      if (!isAuthenticated()) {
        return window.APIClient.response(false, null, "Please log in", 401);
      }

      const res = await window.APIClient.delete(`/cart/${cartItemIdOrProductId}`);
      if (res.success) {
        return await this.getCart();
      }
      return res;
    },

    clearCart: async function() {
      if (!isAuthenticated()) {
        if (window.StorageUtils) window.StorageUtils.writeJSON(CART_KEY, []);
        return window.APIClient.response(true, { items: [] }, null, 200);
      }

      const res = await window.APIClient.delete("/cart");
      return res;
    }
  };
})();

