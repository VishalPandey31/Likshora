/* =========================================================
   LIKSHORA — Product Reviews API Abstraction
   Placeholder interfaces for customer reviews & admin moderation
   ========================================================= */

window.ReviewAPI = (function() {
  const REVIEWS_KEY = "rv_reviews";

  return {
    getProductReviews: async function(productId) {
      const res = await window.APIClient.get(`/products/${productId}/reviews`);
      if (res.success && res.data) {
        return res;
      }
      const reviews = window.StorageUtils ? window.StorageUtils.readJSON(REVIEWS_KEY, []) : [];
      const approved = reviews.filter(r => r.productId === productId && r.status === "Approved");
      return window.APIClient.response(true, { reviews: approved, count: approved.length }, null, 200);
    },

    submitReview: async function(reviewPayload) {
      const res = await window.APIClient.post(`/products/${reviewPayload.productId}/reviews`, reviewPayload);
      if (res.success) return res;

      let reviews = window.StorageUtils ? window.StorageUtils.readJSON(REVIEWS_KEY, []) : [];
      const newReview = Object.assign({
        id: "REV_" + Date.now().toString(36),
        date: new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }),
        status: "Pending Approval"
      }, reviewPayload);

      reviews.unshift(newReview);
      if (window.StorageUtils) window.StorageUtils.writeJSON(REVIEWS_KEY, reviews);
      return window.APIClient.response(true, { review: newReview, message: "Review submitted for moderation" }, null, 201);
    },

    approveReview: async function(reviewId) {
      return await window.APIClient.post(`/admin/reviews/${reviewId}/approve`, {});
    },

    deleteReview: async function(reviewId) {
      return await window.APIClient.delete(`/admin/reviews/${reviewId}`);
    }
  };
})();

