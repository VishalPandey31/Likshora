/* =========================================================
   LIKSHORA — Wishlist API Abstraction
   Placeholder interfaces for customer wishlist items management
   ========================================================= */

window.WishlistAPI = (function() {
  const TOKEN_KEY = "rv_access_token";

  function isAuthenticated() {
    return !!localStorage.getItem(TOKEN_KEY);
  }

  return {
    getWishlist: async function() {
      if (!isAuthenticated()) {
        return window.APIClient.response(true, { items: [], count: 0 }, null, 200);
      }
      const res = await window.APIClient.get("/wishlist");
      if (res.success && res.data) {
        const items = Array.isArray(res.data) ? res.data : (res.data.items || res.data.wishlist_items || []);
        return window.APIClient.response(true, { items: items, count: items.length }, null, res.status);
      }
      return res;
    },

    addToWishlist: async function(product) {
      if (!isAuthenticated()) {
        return window.APIClient.response(false, { redirect: "login" }, "Please log in to save items to your wishlist", 401);
      }
      const productId = typeof product === "object" ? (product.product_id || product.id) : product;
      const res = await window.APIClient.post("/wishlist", { product_id: productId });
      if (res.success) {
        return await this.getWishlist();
      }
      return res;
    },

    removeFromWishlist: async function(productId) {
      if (!isAuthenticated()) {
        return window.APIClient.response(false, null, "Please log in", 401);
      }
      const res = await window.APIClient.delete(`/wishlist/${productId}`);
      if (res.success) {
        return await this.getWishlist();
      }
      return res;
    },

    isInWishlist: async function(productId) {
      if (!isAuthenticated()) return false;
      const res = await window.APIClient.get(`/wishlist/check/${productId}`);
      return res.success && res.data && res.data.in_wishlist;
    },

    moveToCart: async function(wishlistItemId) {
      if (!isAuthenticated()) return window.APIClient.response(false, null, "Please log in", 401);
      return await window.APIClient.post(`/wishlist/${wishlistItemId}/move-to-cart`, {});
    }
  };
})();

