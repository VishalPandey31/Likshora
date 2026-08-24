/* =========================================================
   LIKSHORA — Products & Catalog API Abstraction
   REST API client methods for products, categories, search, & dynamic site content
   ========================================================= */

window.ProductAPI = (function() {
  return {
    getProducts: async function(params = {}) {
      const query = {};
      if (params.category && params.category !== "all") {
        query.category = params.category;
      }
      if (params.search) {
        query.search = params.search;
      }
      if (params.featured) {
        query.featured = true;
      }
      if (params.trending) {
        query.trending = true;
      }
      const res = await window.APIClient.get("/products", query);
      if (res.success && res.data) {
        const products = Array.isArray(res.data) ? res.data : (res.data.products || []);
        return window.APIClient.response(true, { products: products, count: products.length }, null, res.status);
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

    getCategories: async function() {
      const res = await window.APIClient.get("/categories");
      if (res.success && res.data) {
        const categories = Array.isArray(res.data) ? res.data : (res.data.categories || []);
        return window.APIClient.response(true, categories, null, res.status);
      }
      return res;
    },

    getSiteContent: async function() {
      return await window.APIClient.get("/content");
    },

    searchProducts: async function(query) {
      return this.getProducts({ search: query });
    }
  };
})();
