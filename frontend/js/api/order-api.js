/* =========================================================
   LIKSHORA — Orders API Abstraction
   Placeholder interfaces for customer order placement & tracking
   ========================================================= */

window.OrderAPI = (function() {
  return {
    validateCoupon: async function(code, cartSubtotal = 0) {
      return await window.APIClient.post("/coupons/validate", { code: code, cart_subtotal: cartSubtotal });
    },

    createOrder: async function(orderPayload) {
      const res = await window.APIClient.post("/orders", orderPayload);
      if (res.success && res.data) {
        return window.APIClient.response(true, res.data.order || res.data, null, res.status);
      }
      return res;
    },

    getUserOrders: async function() {
      const res = await window.APIClient.get("/orders");
      if (res.success && res.data) {
        const orders = Array.isArray(res.data) ? res.data : (res.data.orders || []);
        return window.APIClient.response(true, orders, null, res.status);
      }
      return res;
    },

    getOrderById: async function(orderId) {
      const res = await window.APIClient.get(`/orders/${orderId}`);
      if (res.success && res.data) {
        return window.APIClient.response(true, res.data.order || res.data, null, res.status);
      }
      return res;
    },

    trackOrder: async function(orderId) {
      const res = await window.APIClient.get(`/orders/${orderId}/tracking`);
      if (res.success && res.data) {
        return window.APIClient.response(true, res.data, null, res.status);
      }
      return await this.getOrderById(orderId);
    },

    cancelOrder: async function(orderId, reason = "") {
      return await window.APIClient.post(`/orders/${orderId}/cancel`, { reason });
    }
  };
})();

