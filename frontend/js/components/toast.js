/* =========================================================
   LIKSHORA — Toast Notification Component
   Global toast notification manager
   ========================================================= */

window.Toast = (function() {
  let toastTimer = null;

  function getToastElement() {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    return toast;
  }

  return {
    show: function(message, duration) {
      const toast = getToastElement();
      toast.textContent = message;
      toast.classList.add("show");

      clearTimeout(toastTimer);
      toastTimer = setTimeout(function() {
        toast.classList.remove("show");
      }, duration || 2200);
    }
  };
})();

// Fallback global helper function
window.showToast = function(msg, duration) {
  window.Toast.show(msg, duration);
};
