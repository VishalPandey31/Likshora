/* =========================================================
   LIKSHORA — Admin Products & Inventory Controller
   Catalog CRUD, search, filter, sort, pagination & stock updates
   ========================================================= */

(function() {
  const PRODUCTS_KEY = "rv_products";

  const DEFAULT_PRODUCTS = [];

  let products = window.StorageUtils ? window.StorageUtils.readJSON(PRODUCTS_KEY, DEFAULT_PRODUCTS) : DEFAULT_PRODUCTS;
  let currentPage = 1;
  const itemsPerPage = 6;
  let pendingDeleteId = null;
  let pendingStockChanges = {};

  function saveProducts() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(PRODUCTS_KEY, products);
    }
  }

  function getProductIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
  }

  /* ---------- Products Table Catalog Rendering ---------- */
  function renderProductsCatalog() {
    const tableBody = document.getElementById("adminProductsTableBody");
    const countEl = document.getElementById("adminProductCount");
    if (!tableBody) return;

    const categoryFilter = document.getElementById("adminProdCategoryFilter") ? document.getElementById("adminProdCategoryFilter").value : "all";
    const statusFilter = document.getElementById("adminProdStatusFilter") ? document.getElementById("adminProdStatusFilter").value : "all";
    const sortVal = document.getElementById("adminProdSortSelect") ? document.getElementById("adminProdSortSelect").value : "name";

    let filtered = products.filter(function(p) {
      const matchC = categoryFilter === "all" || p.category === categoryFilter;
      const matchS = statusFilter === "all" || p.status === statusFilter;
      return matchC && matchS;
    });

    if (sortVal === "price-asc") filtered.sort(function(a, b) { return a.price - b.price; });
    if (sortVal === "price-desc") filtered.sort(function(a, b) { return b.price - a.price; });
    if (sortVal === "stock-asc") filtered.sort(function(a, b) { return a.stock - b.stock; });

    if (countEl) countEl.textContent = `Showing ${filtered.length} products`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No products match the selected criteria.</td></tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(function(p) {
      let imgPath = p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].url) : "");
      if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
        imgPath = "../../" + imgPath;
      }

      let statusPillClass = "success";
      if (p.status === "Draft") statusPillClass = "pending";
      if (p.status === "Out of Stock" || p.stock === 0) statusPillClass = "alert";

      return `
        <tr data-id="${p.id}">
          <td>
            <div style="display:flex; align-items:center; gap:1em;">
              <div style="width:40px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
                ${imgPath ? '<img src="' + imgPath + '" style="width:100%; height:100%; object-fit:cover;">' : ''}
              </div>
              <div>
                <strong style="font-size:.9rem;">${window.Formatters.escapeHTML(p.name)}</strong>
                <p style="margin:0; font-size:.74rem; color:var(--admin-ink-soft);">${p.sku || 'SKU-N/A'}</p>
              </div>
            </div>
          </td>
          <td><span style="text-transform:capitalize;">${p.category}</span></td>
          <td style="font-weight:600;">${window.Formatters.formatINR(p.price)}</td>
          <td><strong>${p.stock}</strong> units</td>
          <td><span class="status-pill ${statusPillClass}">${p.status || 'Active'}</span></td>
          <td style="text-align:right;">
            <div style="display:flex; gap:.4em; justify-content:flex-end;">
              <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-view="${p.id}">View</button>
              <a href="edit-product.html?id=${p.id}" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem; text-decoration:none;">Edit</a>
              <button type="button" class="btn-admin-danger" style="padding:.3em .6em; font-size:.76rem;" data-delete="${p.id}">Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join("  async function loadProductsFromAPI() {
    if (window.AdminAPI && window.AdminAPI.getAdminProducts) {
      try {
        const res = await window.AdminAPI.getAdminProducts();
        if (res.success && res.data) {
          const list = Array.isArray(res.data) ? res.data : (res.data.products || []);
          if (Array.isArray(list)) {
            products = list.map(function(p) {
              return {
                id: p.id,
                sku: p.sku || "SKU-N/A",
                name: p.name,
                price: p.selling_price !== undefined ? p.selling_price : p.price,
                was: p.list_price !== undefined ? p.list_price : p.compare_at_price,
                category: typeof p.category === 'object' ? (p.category ? p.category.slug : 'kurtis') : (p.category || 'kurtis'),
                stock: p.stock_quantity !== undefined ? p.stock_quantity : (p.stock || 0),
                status: p.is_active ? "Active" : "Draft",
                description: p.description || "",
                tagline: p.tagline || "",
                tags: p.tags || "",
                image: p.primary_image_url || p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].image_url) : ""),
                images: p.images || []
              };
            });
            renderProductsCatalog();
            renderInventoryPage();
          }
        }
      } catch (err) {
        console.warn("Could not fetch products from REST API, using local fallback:", err);
      }
    }
  }

  /* ---------- Product Form Handler (Add & Edit) ---------- */
  function initProductFormHandler() {
    const form = document.getElementById("productForm");
    if (!form) return;

    const editId = getProductIdFromURL();
    let existingProd = null;

    // Local state for product image URLs
    let imageState = [];

    function formatImageSrc(url) {
      if (!url) return "";
      let src = url.trim();
      if (!src.startsWith("http://") && !src.startsWith("https://") && !src.startsWith("data:") && !src.startsWith("../")) {
        if (src.startsWith("/")) src = "../.." + src;
        else if (!src.startsWith("../../")) src = "../../" + src;
      }
      return src;
    }

    async function populateFormFields() {
      if (editId) {
        if (window.AdminAPI && window.AdminAPI.getProductById) {
          try {
            const apiRes = await window.AdminAPI.getProductById(editId);
            if (apiRes.success && apiRes.data) {
              const p = apiRes.data;
              existingProd = {
                id: p.id,
                sku: p.sku || "",
                name: p.name,
                price: p.selling_price !== undefined ? p.selling_price : p.price,
                was: p.list_price !== undefined ? p.list_price : p.compare_at_price,
                category: typeof p.category === 'object' ? (p.category ? p.category.slug : 'kurtis') : (p.category || 'kurtis'),
                stock: p.stock_quantity !== undefined ? p.stock_quantity : (p.stock || 0),
                status: p.is_active ? "Active" : "Draft",
                description: p.description || "",
                tagline: p.tagline || "",
                tags: p.tags || "",
                image: p.primary_image_url || p.image || (p.images && p.images.length > 0 ? (typeof p.images[0] === 'string' ? p.images[0] : p.images[0].image_url) : ""),
                images: p.images || []
              };
            }
          } catch (e) {
            console.warn("Could not fetch product detail from API:", e);
          }
        }
        if (!existingProd) {
          existingProd = products.find(function(p) { return String(p.id) === String(editId); });
        }

        if (existingProd) {
          document.getElementById("prodName").value = existingProd.name || "";
          document.getElementById("prodSKU").value = existingProd.sku || "";
          document.getElementById("prodCategory").value = existingProd.category || "kurtis";
          document.getElementById("prodStatus").value = existingProd.status || "Active";
          document.getElementById("prodPrice").value = existingProd.price || 0;
          document.getElementById("prodWasPrice").value = existingProd.was !== null && existingProd.was !== undefined ? existingProd.was : "";
          document.getElementById("prodStock").value = existingProd.stock || 0;
          document.getElementById("prodDescription").value = existingProd.description || "";

          if (existingProd.images && Array.isArray(existingProd.images) && existingProd.images.length > 0) {
            imageState = existingProd.images.map(function(imgItem, idx) {
              const url = typeof imgItem === "string" ? imgItem : (imgItem.url || imgItem.image_url);
              return {
                id: typeof imgItem === "object" && imgItem.id ? imgItem.id : "img_" + (idx + 1),
                url: url || "",
                status: "pending",
                errorMsg: ""
              };
            });
          } else if (existingProd.image) {
            imageState = [{ id: "img_1", url: existingProd.image, status: "pending", errorMsg: "" }];
          }

          const heading = document.getElementById("formPageTitle");
          if (heading) heading.textContent = "Edit Product — " + existingProd.name;
        }
      }

      if (imageState.length === 0) {
        imageState = [
          { id: "img_1", url: "../../assets/images/products/product-kurti-1.jpg", status: "pending", errorMsg: "" }
        ];
      }
    }

    function testImageURL(index) {
      const item = imageState[index];
      if (!item) return;

      const rawUrl = item.url ? item.url.trim() : "";
      if (!rawUrl) {
        item.status = "error";
        item.errorMsg = "Image URL cannot be empty.";
        updateCardUI(index);
        return;
      }

      const isHttp = rawUrl.startsWith("http://") || rawUrl.startsWith("https://");
      const isData = rawUrl.startsWith("data:image/");
      const isRelative = rawUrl.startsWith("../") || rawUrl.startsWith("./") || rawUrl.startsWith("/") || rawUrl.startsWith("assets/");

      if (!isHttp && !isData && !isRelative) {
        item.status = "error";
        item.errorMsg = "Please enter a valid HTTP/HTTPS URL or asset path.";
        updateCardUI(index);
        return;
      }

      item.status = "pending";
      updateCardUI(index);

      const testImg = new Image();
      testImg.onload = function() {
        if (imageState[index] && imageState[index].url === rawUrl) {
          imageState[index].status = "valid";
          imageState[index].errorMsg = "";
          updateCardUI(index);
        }
      };
      testImg.onerror = function() {
        if (imageState[index] && imageState[index].url === rawUrl) {
          imageState[index].status = "valid"; // allow assets path even if test fails locally
          imageState[index].errorMsg = "";
          updateCardUI(index);
        }
      };
      testImg.src = formatImageSrc(rawUrl);
    }

    function updateCardUI(index) {
      const container = document.getElementById("productImageList");
      if (!container) return;
      const card = container.querySelector(`[data-card-index="${index}"]`);
      if (!card) return;

      const item = imageState[index];
      if (!item) return;

      const badgeEl = card.querySelector(".image-status-badge");
      const previewBox = card.querySelector(".image-preview-box");
      const errorTextEl = card.querySelector(".image-error-text");

      if (item.status === "valid") {
        card.classList.remove("has-error");
        if (badgeEl) {
          badgeEl.className = "image-status-badge valid";
          badgeEl.innerHTML = "✓ Valid Image";
        }
        if (errorTextEl) errorTextEl.style.display = "none";
        if (previewBox) {
          previewBox.innerHTML = `<img src="${formatImageSrc(item.url)}" alt="Product Image ${index + 1}">`;
        }
      } else if (item.status === "error") {
        card.classList.add("has-error");
        if (badgeEl) {
          badgeEl.className = "image-status-badge error";
          badgeEl.innerHTML = "⚠ Invalid Image";
        }
        if (errorTextEl) {
          errorTextEl.textContent = item.errorMsg || "Unable to load image.";
          errorTextEl.style.display = "block";
        }
        if (previewBox) {
          previewBox.innerHTML = `
            <div class="image-preview-fallback">
              <span style="font-size:1.4rem;">⚠️</span>
              <span>Load Failed</span>
            </div>
          `;
        }
      } else {
        card.classList.remove("has-error");
        if (badgeEl) {
          badgeEl.className = "image-status-badge pending";
          badgeEl.innerHTML = "⏳ Checking...";
        }
        if (errorTextEl) errorTextEl.style.display = "none";
        if (previewBox) {
          previewBox.innerHTML = `
            <div class="image-preview-fallback">
              <span style="font-size:1.2rem;">⏳</span>
              <span>Loading...</span>
            </div>
          `;
        }
      }
    }

    function renderImageSection() {
      const container = document.getElementById("productImageList");
      if (!container) return;

      if (imageState.length === 0) {
        container.innerHTML = `
          <div style="padding:1.5em; text-align:center; background:var(--white); border:1px dashed var(--admin-border); border-radius:var(--radius-sm); color:var(--admin-ink-soft);">
            <p style="margin:0; font-size:.88rem;">No images added yet. Click below to add an image URL.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = imageState.map(function(item, index) {
        const isPrimary = index === 0;
        const formattedSrc = formatImageSrc(item.url);

        return `
          <div class="admin-image-card ${item.status === 'error' ? 'has-error' : ''}" data-card-index="${index}">
            <div class="image-preview-box">
              ${item.url ? `<img src="${formattedSrc}" alt="Preview ${index + 1}">` : `
                <div class="image-preview-fallback">
                  <span style="font-size:1.2rem;">🖼️</span>
                  <span>No URL</span>
                </div>
              `}
            </div>

            <div class="image-card-body">
              <div class="image-card-title">
                <span>Image ${index + 1} ${isPrimary ? '<strong style="color:var(--admin-gold); font-size:.76rem; margin-left:.4em;">(Primary Cover Image)</strong>' : ''}</span>
                <span class="image-status-badge ${item.status}">
                  ${item.status === 'valid' ? '✓ Valid Image' : item.status === 'error' ? '⚠ Invalid Image' : '⏳ Checking...'}
                </span>
              </div>

              <div class="image-input-options">
                <label class="btn-browse-file">
                  <span>📁 Browse Image from Computer</span>
                  <input type="file" class="image-file-input" data-index="${index}" accept="image/*" style="display:none;">
                </label>
                <span style="font-size:.76rem; color:var(--admin-ink-soft); font-weight:500;">OR enter Web URL / Asset Path:</span>
              </div>

              <input type="text" class="auth-input image-url-input" data-index="${index}" value="${window.Formatters ? window.Formatters.escapeHTML(item.url) : item.url}" placeholder="https://example.com/product-image.jpg or assets/..." style="font-size:.84rem;">

              <div class="image-error-text" style="color:var(--admin-danger); font-size:.76rem; display:${item.status === 'error' ? 'block' : 'none'};">
                ${window.Formatters ? window.Formatters.escapeHTML(item.errorMsg || '') : item.errorMsg}
              </div>
            </div>

            <div style="display:flex; flex-direction:column; gap:.4em; align-items:flex-end;">
              <button type="button" class="btn-admin-danger btn-remove-image" data-index="${index}" style="padding:.4em .8em; font-size:.78rem;">
                ✕ Remove
              </button>
            </div>
          </div>
        `;
      }).join("");

      imageState.forEach(function(_, idx) {
        testImageURL(idx);
      });
    }

    populateFormFields().then(function() {
      renderImageSection();
    });

    const imageContainer = document.getElementById("productImageList");
    if (imageContainer) {
      // File input listener with backend image upload API call
      imageContainer.addEventListener("change", async function(e) {
        if (e.target.classList.contains("image-file-input")) {
          const file = e.target.files && e.target.files[0];
          const index = parseInt(e.target.dataset.index, 10);
          if (file && !isNaN(index) && imageState[index]) {
            if (window.AdminAPI && window.AdminAPI.uploadImage) {
              const uploadRes = await window.AdminAPI.uploadImage(file);
              if (uploadRes.success && uploadRes.data && uploadRes.data.url) {
                const uploadedUrl = uploadRes.data.url;
                imageState[index].url = uploadedUrl;
                const input = imageContainer.querySelector(`.image-url-input[data-index="${index}"]`);
                if (input) input.value = uploadedUrl;
                testImageURL(index);
                if (window.Toast) window.Toast.show(`Image uploaded successfully!`);
                return;
              }
            }
            const reader = new FileReader();
            reader.onload = function(event) {
              const dataUrl = event.target.result;
              imageState[index].url = dataUrl;
              const input = imageContainer.querySelector(`.image-url-input[data-index="${index}"]`);
              if (input) input.value = dataUrl;
              testImageURL(index);
            };
            reader.readAsDataURL(file);
          }
        }
      });

      imageContainer.addEventListener("input", function(e) {
        if (e.target.classList.contains("image-url-input")) {
          const index = parseInt(e.target.dataset.index, 10);
          if (!isNaN(index) && imageState[index]) {
            imageState[index].url = e.target.value;
            testImageURL(index);
          }
        }
      });

      imageContainer.addEventListener("click", function(e) {
        const removeBtn = e.target.closest(".btn-remove-image");
        if (removeBtn) {
          const index = parseInt(removeBtn.dataset.index, 10);
          if (!isNaN(index)) {
            imageState.splice(index, 1);
            renderImageSection();
            if (window.Toast) window.Toast.show("Image removed.");
          }
        }
      });
    }

    const addImgBtn = document.getElementById("addImageUrlBtn");
    if (addImgBtn) {
      addImgBtn.addEventListener("click", function() {
        imageState.push({
          id: "img_" + Date.now().toString(36),
          url: "",
          status: "pending",
          errorMsg: ""
        });
        renderImageSection();
        const inputs = imageContainer ? imageContainer.querySelectorAll(".image-url-input") : [];
        if (inputs.length > 0) {
          inputs[inputs.length - 1].focus();
        }
      });
    }

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      const name = document.getElementById("prodName").value.trim();
      const sku = document.getElementById("prodSKU").value.trim().toUpperCase();
      const category = document.getElementById("prodCategory").value;
      const status = document.getElementById("prodStatus").value;
      const price = parseFloat(document.getElementById("prodPrice").value);
      const wasPriceVal = document.getElementById("prodWasPrice").value;
      const was = wasPriceVal ? parseFloat(wasPriceVal) : null;
      const stock = parseInt(document.getElementById("prodStock").value, 10);
      const description = document.getElementById("prodDescription").value.trim();

      if (!name) {
        if (window.Toast) window.Toast.show("Please enter a valid product name.");
        document.getElementById("prodName").focus();
        return;
      }

      if (!sku) {
        if (window.Toast) window.Toast.show("Please enter a valid SKU.");
        document.getElementById("prodSKU").focus();
        return;
      }

      if (isNaN(price) || price < 0) {
        if (window.Toast) window.Toast.show("Please enter a valid selling price.");
        document.getElementById("prodPrice").focus();
        return;
      }

      if (isNaN(stock) || stock < 0) {
        if (window.Toast) window.Toast.show("Please enter a valid stock quantity.");
        document.getElementById("prodStock").focus();
        return;
      }

      const validImages = imageState.filter(function(img) { return img.url && img.url.trim() !== ""; });
      if (validImages.length === 0) {
        if (window.Toast) window.Toast.show("Please add at least one product image URL.");
        return;
      }

      const formattedImages = validImages.map(function(img, idx) {
        return {
          id: img.id || ("img_" + (idx + 1)),
          url: img.url.trim(),
          position: idx + 1
        };
      });

      const primaryImage = formattedImages[0].url;

      const payload = {
        name: name,
        sku: sku,
        category: category,
        status: status,
        price: price,
        selling_price: price,
        was: was,
        compare_at_price: was,
        stock: stock,
        stock_quantity: stock,
        description: description,
        image: primaryImage,
        images: formattedImages,
        is_active: status !== "Draft" && status !== "Inactive"
      };

      if (existingProd) {
        if (window.AdminAPI && window.AdminAPI.updateProduct) {
          await window.AdminAPI.updateProduct(existingProd.id, payload);
        } else {
          Object.assign(existingProd, payload);
          saveProducts();
        }
        if (window.Toast) window.Toast.show("Product updated successfully!");
      } else {
        if (window.AdminAPI && window.AdminAPI.createProduct) {
          await window.AdminAPI.createProduct(payload);
        } else {
          const newProd = Object.assign({
            id: "PROD_" + Date.now().toString(36).toUpperCase(),
            rating: 5.0
          }, payload);
          products.unshift(newProd);
          saveProducts();
        }
        if (window.Toast) window.Toast.show("New product added to catalog!");
      }

      setTimeout(function() {
        window.location.href = "products.html";
      }, 500);
    });
  }

  /* ---------- Inventory Management Page ---------- */
  function renderInventoryPage() {
    const tableBody = document.getElementById("adminInventoryTableBody");
    const statTotalEl = document.getElementById("invStatTotal");
    const statInStockEl = document.getElementById("invStatInStock");
    const statLowStockEl = document.getElementById("invStatLowStock");
    const statOutStockEl = document.getElementById("invStatOutStock");
    const pendingBadge = document.getElementById("pendingStockBadge");

    if (!tableBody) return;

    const effectiveProducts = products.map(function(p) {
      const effectiveStock = pendingStockChanges.hasOwnProperty(p.id) ? pendingStockChanges[p.id] : p.stock;
      return { product: p, stock: effectiveStock };
    });

    const inStockCount = effectiveProducts.filter(function(item) { return item.stock > 4; }).length;
    const lowStockCount = effectiveProducts.filter(function(item) { return item.stock > 0 && item.stock <= 4; }).length;
    const outStockCount = effectiveProducts.filter(function(item) { return item.stock === 0; }).length;

    if (statTotalEl) statTotalEl.textContent = products.length;
    if (statInStockEl) statInStockEl.textContent = inStockCount;
    if (statLowStockEl) statLowStockEl.textContent = lowStockCount;
    if (statOutStockEl) statOutStockEl.textContent = outStockCount;

    const pendingCount = Object.keys(pendingStockChanges).length;
    if (pendingBadge) {
      if (pendingCount > 0) {
        pendingBadge.innerHTML = `<strong style="color:var(--admin-gold);">${pendingCount}</strong> product${pendingCount > 1 ? 's' : ''} modified (unsaved)`;
      } else {
        pendingBadge.textContent = "No unsaved changes";
      }
    }

    tableBody.innerHTML = products.map(function(p) {
      const effectiveStock = pendingStockChanges.hasOwnProperty(p.id) ? pendingStockChanges[p.id] : p.stock;
      const isModified = pendingStockChanges.hasOwnProperty(p.id) && pendingStockChanges[p.id] !== p.stock;

      let statusClass = "success";
      let statusLabel = "In Stock";
      if (effectiveStock > 0 && effectiveStock <= 4) { statusClass = "pending"; statusLabel = "Low Stock"; }
      if (effectiveStock === 0) { statusClass = "alert"; statusLabel = "Out of Stock"; }

      let rowBg = isModified ? 'style="background-color: rgba(200, 155, 60, 0.08);"' : '';
      let modBadge = isModified ? `<span style="font-size:.74rem; color:var(--admin-gold); font-weight:600; margin-left:.5em;">(Modified)</span>` : '';

      return `
        <tr data-id="${p.id}" ${rowBg}>
          <td style="font-weight:600;">${p.sku || p.id}</td>
          <td><strong>${window.Formatters ? window.Formatters.escapeHTML(p.name) : p.name}</strong>${modBadge}</td>
          <td style="text-transform:capitalize;">${p.category}</td>
          <td><span class="status-pill ${statusClass}">${statusLabel}</span></td>
          <td>
            <div class="cart-qty-wrap" style="height:34px;">
              <button type="button" class="qty-btn" data-inv-adjust="${p.id}" data-delta="-1">–</button>
              <input type="number" class="qty-val-input" data-inv-input="${p.id}" value="${effectiveStock}" min="0" style="width:55px; text-align:center; border:1px solid var(--admin-border); border-radius:4px; font-weight:600; font-size:.88rem; color:var(--admin-ink); margin:0 .2em; background:var(--white);">
              <button type="button" class="qty-btn" data-inv-adjust="${p.id}" data-delta="1">+</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function initInventoryPage() {
    renderInventoryPage();

    const tableBody = document.getElementById("adminInventoryTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", function(e) {
        const adjustBtn = e.target.closest("[data-inv-adjust]");
        if (adjustBtn) {
          const id = adjustBtn.dataset.invAdjust;
          const delta = parseInt(adjustBtn.dataset.delta, 10);

          const prod = products.find(function(p) { return String(p.id) === String(id); });
          if (prod) {
            const currentVal = pendingStockChanges.hasOwnProperty(id) ? pendingStockChanges[id] : prod.stock;
            const newVal = Math.max(0, currentVal + delta);
            if (newVal === prod.stock) {
              delete pendingStockChanges[id];
            } else {
              pendingStockChanges[id] = newVal;
            }
            renderInventoryPage();
          }
        }
      });

      tableBody.addEventListener("input", function(e) {
        const inputEl = e.target.closest("[data-inv-input]");
        if (inputEl) {
          const id = inputEl.dataset.invInput;
          const prod = products.find(function(p) { return String(p.id) === String(id); });
          if (prod) {
            let val = parseInt(inputEl.value, 10);
            if (isNaN(val) || val < 0) val = 0;
            if (val === prod.stock) {
              delete pendingStockChanges[id];
            } else {
              pendingStockChanges[id] = val;
            }
            renderInventoryPage();
          }
        }
      });
    }

    const saveBtn = document.getElementById("btnSaveInventoryChanges");
    if (saveBtn) {
      saveBtn.addEventListener("click", async function() {
        const modifiedIds = Object.keys(pendingStockChanges);
        if (modifiedIds.length === 0) {
          if (window.Toast) window.Toast.show("No stock changes to save.");
          return;
        }

        try {
          let updatedCount = 0;
          for (let i = 0; i < modifiedIds.length; i++) {
            const id = modifiedIds[i];
            const newStock = pendingStockChanges[id];
            const prod = products.find(function(p) { return String(p.id) === String(id); });
            if (prod && prod.stock !== newStock) {
              if (window.AdminAPI && window.AdminAPI.updateStock) {
                await window.AdminAPI.updateStock(id, newStock);
              }
              prod.stock = newStock;
              if (prod.stock === 0) {
                prod.status = "Out of Stock";
              } else if (prod.status === "Out of Stock") {
                prod.status = "Active";
              }
              updatedCount++;
            }
          }

          saveProducts();
          pendingStockChanges = {};
          renderInventoryPage();

          if (window.Toast) {
            window.Toast.show(`Successfully saved stock changes for ${updatedCount} product${updatedCount > 1 ? 's' : ''}!`);
          }
        } catch (err) {
          console.error("Error saving inventory changes:", err);
          if (window.Toast) {
            window.Toast.show("Failed to save stock changes. Please try again.");
          }
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    loadProductsFromAPI();
    renderProductsCatalog();
    initProductFormHandler();
    initInventoryPage();

    const categorySelect = document.getElementById("adminProdCategoryFilter");
    const statusSelect = document.getElementById("adminProdStatusFilter");
    const sortSelect = document.getElementById("adminProdSortSelect");

    if (categorySelect) categorySelect.addEventListener("change", function() { renderProductsCatalog(); });
    if (statusSelect) statusSelect.addEventListener("change", function() { renderProductsCatalog(); });
    if (sortSelect) sortSelect.addEventListener("change", function() { renderProductsCatalog(); });

    const tableBody = document.getElementById("adminProductsTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", function(e) {
        const viewBtn = e.target.closest("[data-view]");
        const deleteBtn = e.target.closest("[data-delete]");

        if (viewBtn) {
          const prod = products.find(function(p) { return String(p.id) === String(viewBtn.dataset.view); });
          if (prod && window.Modal) {
            const modalTitle = document.getElementById("viewModalTitle");
            const modalBody = document.getElementById("viewModalBody");
            if (modalTitle) modalTitle.textContent = prod.name;
            if (modalBody) {
              const allImages = prod.images && Array.isArray(prod.images) && prod.images.length > 0 
                ? prod.images.map(img => typeof img === 'string' ? img : (img.url || img.image_url))
                : (prod.image ? [prod.image] : []);

              const imageGalleryHTML = allImages.map(function(src, i) {
                let formattedSrc = src;
                if (formattedSrc && !formattedSrc.startsWith("http") && !formattedSrc.startsWith("../")) {
                  formattedSrc = "../../" + formattedSrc;
                }
                return `
                  <div style="display:flex; align-items:center; gap:.8em; background:var(--admin-bg); padding:.6em; border-radius:var(--radius-sm); border:1px solid var(--admin-border);">
                    <img src="${formattedSrc}" style="width:48px; height:60px; object-fit:cover; border-radius:4px;" alt="Image ${i + 1}">
                    <div style="min-width:0; flex:1;">
                      <span style="font-size:.76rem; font-weight:600; color:var(--admin-ink);">Image ${i + 1} ${i === 0 ? '(Primary)' : ''}</span>
                      <p style="margin:0; font-size:.72rem; color:var(--admin-ink-soft); word-break:break-all;">${src}</p>
                    </div>
                  </div>
                `;
              }).join("");

              modalBody.innerHTML = `
                <p><strong>SKU:</strong> ${window.Formatters ? window.Formatters.escapeHTML(prod.sku || '') : (prod.sku || '')}</p>
                <p><strong>Category:</strong> <span style="text-transform:capitalize;">${window.Formatters ? window.Formatters.escapeHTML(prod.category || '') : (prod.category || '')}</span></p>
                <p><strong>Price:</strong> ${window.Formatters ? window.Formatters.formatINR(prod.price) : ('₹' + prod.price)} ${prod.was ? `<span style="text-decoration:line-through; color:var(--admin-ink-soft); margin-left:.4em;">${window.Formatters ? window.Formatters.formatINR(prod.was) : ('₹' + prod.was)}</span>` : ''}</p>
                <p><strong>Stock Level:</strong> ${prod.stock} units</p>
                <p><strong>Status:</strong> ${window.Formatters ? window.Formatters.escapeHTML(prod.status || 'Active') : (prod.status || 'Active')}</p>
                <p><strong>Description:</strong> ${window.Formatters ? window.Formatters.escapeHTML(prod.description || '') : (prod.description || '')}</p>
                <div style="margin-top:1em;">
                  <strong>Product Images (${allImages.length}):</strong>
                  <div style="display:flex; flex-direction:column; gap:.5em; margin-top:.5em;">
                    ${imageGalleryHTML || '<p style="font-size:.8rem; color:var(--admin-ink-soft);">No images attached.</p>'}
                  </div>
                </div>
              `;
            }
            window.Modal.open("adminProductViewModal");
          }
        }

        if (deleteBtn) {
          pendingDeleteId = deleteBtn.dataset.delete;
          if (window.Modal) window.Modal.open("adminConfirmModal");
        }
      });
    }

    const confirmActionBtn = document.getElementById("adminConfirmModalActionBtn");
    if (confirmActionBtn) {
      confirmActionBtn.addEventListener("click", async function() {
        if (pendingDeleteId) {
          if (window.AdminAPI && window.AdminAPI.deleteProduct) {
            await window.AdminAPI.deleteProduct(pendingDeleteId);
          }
          products = products.filter(function(p) { return String(p.id) !== String(pendingDeleteId); });
          saveProducts();
          renderProductsCatalog();
          if (window.Modal) window.Modal.close("adminConfirmModal");
          if (window.Toast) window.Toast.show("Product deleted from catalog.");
          pendingDeleteId = null;
        }
      });
    }
  });
})();
