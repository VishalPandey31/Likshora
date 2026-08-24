/* =========================================================
   LIKSHORA — Loader Component
   Reusable loading spinner for async operations and page loads
   ========================================================= */

window.Loader = (function() {
  function createSpinnerElement() {
    const spinner = document.createElement("div");
    spinner.className = "rv-loader-spinner";
    spinner.setAttribute("aria-label", "Loading");
    spinner.innerHTML = `
      <div class="rv-loader-ring"></div>
      <style>
        .rv-loader-spinner {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2em;
        }
        .rv-loader-ring {
          width: 36px;
          height: 36px;
          border: 3px solid rgba(200, 155, 60, 0.2);
          border-top-color: var(--gold, #C89B3C);
          border-radius: 50%;
          animation: rvSpin 0.8s linear infinite;
        }
        @keyframes rvSpin {
          to { transform: rotate(360deg); }
        }
      </style>
    `;
    return spinner;
  }

  return {
    show: function(targetContainer) {
      const container = typeof targetContainer === "string" 
        ? document.getElementById(targetContainer) 
        : targetContainer || document.body;

      if (!container) return;

      let loader = container.querySelector(".rv-loader-spinner");
      if (!loader) {
        loader = createSpinnerElement();
        container.appendChild(loader);
      }
      loader.style.display = "flex";
    },

    hide: function(targetContainer) {
      const container = typeof targetContainer === "string" 
        ? document.getElementById(targetContainer) 
        : targetContainer || document.body;

      if (!container) return;

      const loader = container.querySelector(".rv-loader-spinner");
      if (loader) {
        loader.style.display = "none";
      }
    }
  };
})();
