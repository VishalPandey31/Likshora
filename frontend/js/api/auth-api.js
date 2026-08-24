/* =========================================================
   LIKSHORA — Customer Auth API Abstraction
   Placeholder interfaces for user registration, authentication & sessions
   ========================================================= */

window.AuthAPI = (function() {
  const SESSION_KEY = "rv_current_user";
  const TOKEN_KEY = "rv_access_token";

  return {
    signup: async function(userData) {
      return await window.APIClient.post("/auth/signup", {
        email: userData.email,
        password: userData.password,
        name: userData.name || userData.fullName || "",
        phone: userData.phone || ""
      });
    },

    login: async function(credentials) {
      const email = credentials.email || credentials.identity;
      const password = credentials.password;
      const res = await window.APIClient.post("/auth/login", { email, password });

      if (res.success && res.data) {
        if (res.data.access_token) {
          localStorage.setItem(TOKEN_KEY, res.data.access_token);
        }
        if (res.data.user) {
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(SESSION_KEY, res.data.user);
          } else {
            localStorage.setItem(SESSION_KEY, JSON.stringify(res.data.user));
          }
        }
      }
      return res;
    },

    resendVerification: async function(email) {
      return await window.APIClient.post("/auth/resend-verification", { email: email });
    },

    verifyEmail: async function(otpCode) {
      // Supabase Email verification is done via email confirmation link
      return window.APIClient.response(true, { message: "Email verification processed" }, null, 200);
    },

    resetPassword: async function(payload) {
      return await window.APIClient.post("/auth/reset-password", payload);
    },

    updatePassword: async function(payload) {
      return await window.APIClient.post("/auth/update-password", payload);
    },

    getCurrentUser: async function() {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        return window.APIClient.response(false, null, "Unauthenticated", 401);
      }
      const res = await window.APIClient.get("/auth/me");
      if (res.success && res.data && res.data.user) {
        if (window.StorageUtils) {
          window.StorageUtils.writeJSON(SESSION_KEY, res.data.user);
        } else {
          localStorage.setItem(SESSION_KEY, JSON.stringify(res.data.user));
        }
      }
      return res;
    },

    getProfile: async function() {
      return await window.APIClient.get("/profile");
    },

    updateProfile: async function(profileData) {
      return await window.APIClient.put("/profile", profileData);
    },

    logout: async function() {
      const res = await window.APIClient.post("/auth/logout", {});
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(SESSION_KEY);
      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(SESSION_KEY, null);
      }
      return res;
    }
  };
})();

