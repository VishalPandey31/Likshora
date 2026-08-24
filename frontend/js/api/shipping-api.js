/* =========================================================
   LIKSHORA — Shipping & Logistics API Abstraction
   Placeholder interfaces for shipping calculation & courier tracking
   ========================================================= */

window.ShippingAPI = (function() {
  return {
    calculateShippingFee: async function(pincode, cartTotal = 0) {
      const fee = cartTotal >= 999 ? 0 : 99;
      return window.APIClient.response(true, { fee: fee, service: "Standard Express Delivery", estDays: "3-5 Business Days" }, null, 200);
    },

    getTrackingInfo: async function(orderId) {
      const res = await window.APIClient.get(`/orders/${orderId}/tracking`);
      if (res.success && res.data) {
        return window.APIClient.response(true, res.data, null, res.status);
      }
      return res;
    },

    syncTracking: async function(shipmentId) {
      return await window.APIClient.post(`/shipments/${shipmentId}/tracking/sync`, {});
    }
  };
})();

