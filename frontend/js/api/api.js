/* =========================================================
   LIKSHORA — Base API Client Abstraction
   Standard response wrapper & simulated async fetch helper
   Designed for seamless future backend/Flask/Supabase integration
   ========================================================= */

window.APIClient = (function () {
  function getBaseURL() {
    const configBase = window.RV_CONFIG && window.RV_CONFIG.API_BASE_URL ? window.RV_CONFIG.API_BASE_URL : "";
    return configBase.replace(/\/+$/, "") + "/api/v1";
  }

  function getAuthHeader() {
    const tokenKey = (window.RV_CONFIG && window.RV_CONFIG.STORAGE_KEYS && window.RV_CONFIG.STORAGE_KEYS.TOKEN) || "rv_access_token";
    let token = null;
    try {
      // Token is stored via StorageUtils.writeJSON which JSON.stringify's the value.
      // We must JSON.parse it back to get the raw token string.
      const raw = localStorage.getItem(tokenKey);
      if (raw) token = JSON.parse(raw);
    } catch (e) {
      // Fallback: use raw value if it's not valid JSON
      token = localStorage.getItem(tokenKey);
    }
    return token ? { "Authorization": `Bearer ${token}` } : {};
  }

  function createResponse(success, data, error = null, status = 200) {
    return {
      success: !!success,
      data: data !== undefined ? data : null,
      error: error,
      status: status,
      timestamp: new Date().toISOString()
    };
  }

  async function request(endpoint, options = {}) {
    const url = getBaseURL() + (endpoint.startsWith("/") ? endpoint : "/" + endpoint);
    const headers = Object.assign(
      {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      getAuthHeader(),
      options.headers || {}
    );

    const config = Object.assign({}, options, { headers });

    try {
      const res = await fetch(url, config);
      let resData = null;
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        resData = await res.json();
      } else {
        const text = await res.text();
        resData = { message: text };
      }

      if (!res.ok) {
        const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
        const rawErr = (resData && (resData.error !== undefined ? resData.error : resData.message)) || resData;
        const errMsg = normalizeFn ? normalizeFn(rawErr, `Request failed with status ${res.status}`) : `Request failed with status ${res.status}`;
        if (res.status === 401) {
          console.warn("APIClient: 401 Unauthorized encountered.");

          // Production-grade Session expiry management
          if (window.Toast) {
            window.Toast.show("Your session has securely expired. Please log in again to continue.", "error");
          } else {
            alert("Your session has securely expired. Please log in again to continue.");
          }
          // Redirect gracefully — use absolute paths to avoid Vercel 404s
          setTimeout(() => {
            if (!window.location.pathname.includes("login")) {
              // Detect admin vs customer context and redirect accordingly
              if (window.location.pathname.includes("/admin")) {
                window.location.href = "/admin/pages/login.html?session_expired=true";
              } else {
                window.location.href = "/pages/auth/login.html?session_expired=true";
              }
            }
          }, 2500);
        }
        return createResponse(false, resData, errMsg, res.status);
      }

      // If backend returns { success: true, data: ... }, unwrap or normalize
      if (resData && typeof resData === "object" && "success" in resData) {
        const normalizeFn = window.normalizeAuthError || (window.Helpers && window.Helpers.normalizeError);
        const normErr = resData.error ? (normalizeFn ? normalizeFn(resData.error) : resData.error) : null;
        return createResponse(resData.success, resData.data !== undefined ? resData.data : resData, normErr, res.status);
      }

      return createResponse(true, resData, null, res.status);
    } catch (err) {
      console.error("APIClient Network Error:", err);
      const isConnError = err && err.message && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError"));
      const userMsg = isConnError
        ? `Unable to connect to backend server at ${getBaseURL()}. Please ensure the Flask server is running.`
        : (err.message || "Network connection failed");
      return createResponse(false, null, userMsg, 500);
    }
  }

  return {
    getBaseURL: getBaseURL,
    response: createResponse,
    request: request,
    get: function (endpoint, params = {}) {
      let queryString = "";
      if (params && Object.keys(params).length > 0) {
        const queryParts = [];
        for (const key in params) {
          if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
            queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
          }
        }
        if (queryParts.length > 0) {
          queryString = "?" + queryParts.join("&");
        }
      }
      return request(endpoint + queryString, { method: "GET" });
    },
    post: function (endpoint, body = {}) {
      return request(endpoint, { method: "POST", body: JSON.stringify(body) });
    },
    put: function (endpoint, body = {}) {
      return request(endpoint, { method: "PUT", body: JSON.stringify(body) });
    },
    patch: function (endpoint, body = {}) {
      return request(endpoint, { method: "PATCH", body: JSON.stringify(body) });
    },
    delete: function (endpoint, body = null) {
      const options = { method: "DELETE" };
      if (body) options.body = JSON.stringify(body);
      return request(endpoint, options);
    }
  };
})();

