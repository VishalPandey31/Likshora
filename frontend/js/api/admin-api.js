/* =========================================================
   LIKSHORA — Admin Portal API Abstraction
   Direct REST backend API communication for catalog CRUD, content & settings
   ========================================================= */

window.AdminAPI = (function() {
  return {
    getDashboardMetrics: async function() {
      return await window.APIClient.get("/admin/dashboard");
    },

    getAdminProducts: async function() {
      const res = await window.APIClient.get("/products", { include_inactive: "true" });
      if (res.success && res.data) {
        const products = Array.isArray(res.data) ? res.data : (res.data.products || []);
        return window.APIClient.response(true, products, null, res.status);
      }
      return res;
    },

    getProductById: async function(id) {
      const res = await window.APIClient.get(`/products/${id}`);
      if (res.success && res.data) {
        const product = res.data.product || res.data;
        return window.APIClient.response(true, product, null, res.status);
      }
      return res;
    },

    createProduct: async function(productData) {
      return await window.APIClient.post("/products", productData);
    },

    updateProduct: async function(id, productData) {
      return await window.APIClient.put(`/products/${id}`, productData);
    },

    deleteProduct: async function(id) {
      return await window.APIClient.delete(`/products/${id}`);
    },

    updateStock: async function(id, stockQuantity) {
      return await window.APIClient.patch(`/products/${id}/stock`, { stock_quantity: stockQuantity });
    },

    uploadImage: async function(file) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const headers = {};
        const token = window.StorageUtils ? window.StorageUtils.readJSON("rv_auth_token", null) : null;
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${window.API_BASE_URL || "/api/v1"}/admin/upload`, {
          method: "POST",
          headers: headers,
          body: formData
        });

        const data = await response.json();
        return window.APIClient.response(response.ok, data.data || data, data.message || null, response.status);
      } catch (err) {
        return window.APIClient.response(false, null, err.message || "Image upload failed", 500);
      }
    },

    getCategories: async function() {
      const res = await window.APIClient.get("/categories", { include_inactive: "true" });
      if (res.success && res.data) {
        const categories = Array.isArray(res.data) ? res.data : (res.data.categories || []);
        return window.APIClient.response(true, categories, null, res.status);
      }
      return res;
    },

    createCategory: async function(categoryData) {
      return await window.APIClient.post("/categories", categoryData);
    },

    updateCategory: async function(id, categoryData) {
      return await window.APIClient.put(`/categories/${id}`, categoryData);
    },

    deleteCategory: async function(id) {
      return await window.APIClient.delete(`/categories/${id}`);
    },

    getSiteContent: async function() {
      return await window.APIClient.get("/content");
    },

    updateSiteContent: async function(contentData) {
      return await window.APIClient.put("/admin/content", contentData);
    },

    getAdminOrders: async function(params = {}) {
      return await window.APIClient.get("/admin/orders", params);
    },

    updateOrderStatus: async function(orderId, status) {
      return await window.APIClient.patch(`/admin/orders/${orderId}/status`, { status });
    },

    fulfillShiprocketOrder: async function(orderId, weight = 0.5, length = 10, breadth = 10, height = 10) {
      return await window.APIClient.post(`/admin/orders/${orderId}/fulfill-shiprocket`, {
        weight, length, breadth, height
      });
    },

    getCustomers: async function(params = {}) {
      return await window.APIClient.get("/admin/customers", params);
    },

    getCustomerById: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}`);
    },

    getCustomerOrders: async function(id, params = {}) {
      return await window.APIClient.get(`/admin/customers/${id}/orders`, params);
    },

    getCustomerPayments: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/payments`);
    },

    getCustomerAddresses: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/addresses`);
    },

    getCustomerCart: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/cart`);
    },

    getCustomerWishlist: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/wishlist`);
    },

    getCustomerSearchHistory: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/search-history`);
    },

    getCustomerReviews: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/reviews`);
    },

    getCustomerLoginLogs: async function(id) {
      return await window.APIClient.get(`/admin/customers/${id}/login-logs`);
    },

    updateCustomerStatus: async function(id, is_active) {
      return await window.APIClient.patch(`/admin/customers/${id}/status`, { is_active });
    },

    getAdminReviews: async function(params = {}) {
      return await window.APIClient.get("/admin/reviews", params);
    },

    updateReviewStatus: async function(id, status) {
      return await window.APIClient.patch(`/admin/reviews/${id}/status`, { status });
    },

    deleteReview: async function(id) {
      return await window.APIClient.delete(`/admin/reviews/${id}`);
    }
  };
})();
