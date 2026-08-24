/* =========================================================
   LIKSHORA — Payment Gateway API Abstraction
   Placeholder interfaces for simulated payment intent & verification
   ========================================================= */

window.PaymentAPI = (function() {
  return {
    getPaymentMethods: async function() {
      return window.APIClient.response(true, [
        { id: "razorpay", name: "Razorpay (Cards, UPI, Netbanking, Wallets)", icon: "💳" },
        { id: "cod", name: "Cash on Delivery (COD)", icon: "💵" }
      ], null, 200);
    },

    createRazorpayOrder: async function(orderId) {
      return await window.APIClient.post("/payments/razorpay/create-order", {
        order_id: orderId
      });
    },

    verifyRazorpayPayment: async function(paymentResponse, orderId = null) {
      return await window.APIClient.post("/payments/razorpay/verify", {
        razorpay_order_id: paymentResponse.razorpay_order_id,
        razorpay_payment_id: paymentResponse.razorpay_payment_id,
        razorpay_signature: paymentResponse.razorpay_signature,
        order_id: orderId || paymentResponse.order_id
      });
    },

    getPaymentDetails: async function(paymentId) {
      return await window.APIClient.get(`/payments/${paymentId}`);
    }
  };
})();

