/* =========================================================
   LIKSHORA — Admin Categories Controller
   Category CRUD, image selection, active/inactive state & REST API integration
   ========================================================= */

(function() {
  const CATEGORIES_KEY = "rv_categories";

  const DEFAULT_CATEGORIES = [
    { id: "cat_kurtis", name: "Printed Kurtis", slug: "kurtis", description: "Breathable cotton dailywear kurtis", status: "Active", productCount: 12, image: "../../assets/images/products/product-kurti-1.jpg" },
    { id: "cat_sets", name: "Kurta Sets", slug: "sets", description: "Paired with matching dupattas and bottoms", status: "Active", productCount: 8, image: "../../assets/images/products/product-kurti-2.jpg" },
    { id: "cat_coords", name: "Co-ord Sets", slug: "coords", description: "Contemporary short kurtis paired with flared trousers", status: "Active", productCount: 6, image: "../../assets/images/products/product-kurti-3.jpg" },
    { id: "cat_festive", name: "Festive Edit", slug: "festive", description: "Rich maroons, zari gold highlights for celebrations", status: "Active", productCount: 10, image: "../../assets/images/products/product-kurti-5.jpg" }
  ];

  let categories = window.StorageUtils ? window.StorageUtils.readJSON(CATEGORIES_KEY, DEFAULT_CATEGORIES) : DEFAULT_CATEGORIES;
  let pendingDeleteId = null;
  let editingCategoryId = null;

  function saveCategories() {
    if (window.StorageUtils) {
      window.StorageUtils.writeJSON(CATEGORIES_KEY, categories);
    }
  }

  async function loadCategoriesFromAPI() {
    if (window.AdminAPI && window.AdminAPI.getCategories) {
      try {
        const res = await window.AdminAPI.getCategories();
        if (res.success && res.data) {
          const list = Array.isArray(res.data) ? res.data : (res.data.categories || []);
          if (list.length > 0) {
            categories = list.map(function(c) {
              return {
                id: c.id,
                name: c.name,
                slug: c.slug,
                description: c.description || "",
                status: c.is_active ? "Active" : "Inactive",
                productCount: c.products_count || 0,
                image: c.image_url || c.image || "../../assets/images/products/product-kurti-1.jpg"
              };
            });
            renderCategoriesTable();
          }
        }
      } catch (err) {
        console.warn("Could not fetch categories from REST API:", err);
      }
    }
  }

  function renderCategoriesTable() {
    const tableBody = document.getElementById("adminCategoriesTableBody");
    const countEl = document.getElementById("adminCategoryCount");
    if (!tableBody) return;

    if (countEl) countEl.textContent = `Showing ${categories.length} categories`;

    if (categories.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:3em; color:var(--admin-ink-soft);">No categories found. Click "+ Add Category" to create one.</td></tr>`;
      return;
    }

    tableBody.innerHTML = categories.map(function(cat) {
      let imgPath = cat.image;
      if (imgPath && !imgPath.startsWith("http") && !imgPath.startsWith("../")) {
        imgPath = "../../" + imgPath;
      }

      const statusPillClass = cat.status === "Active" ? "success" : "alert";

      return `
        <tr data-id="${cat.id}">
          <td>
            <div style="display:flex; align-items:center; gap:1em;">
              <div style="width:40px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
                ${imgPath ? '<img src="' + imgPath + '" style="width:100%; height:100%; object-fit:cover;">' : ''}
              </div>
              <div>
                <strong style="font-size:.92rem;">${window.Formatters ? window.Formatters.escapeHTML(cat.name) : cat.name}</strong>
                <p style="margin:0; font-size:.74rem; color:var(--admin-ink-soft);">${cat.description || ''}</p>
              </div>
            </div>
          </td>
          <td><code style="font-size:.82rem;">${cat.slug}</code></td>
          <td><strong>${cat.productCount || 0}</strong> styles</td>
          <td><span class="status-pill ${statusPillClass}">${cat.status || 'Active'}</span></td>
          <td style="text-align:right;">
            <div style="display:flex; gap:.4em; justify-content:flex-end;">
              <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-toggle-status="${cat.id}">
                ${cat.status === 'Active' ? 'Deactivate' : 'Activate'}
              </button>
              <button type="button" class="btn-admin-secondary" style="padding:.3em .6em; font-size:.76rem;" data-edit-cat="${cat.id}">Edit</button>
              <button type="button" class="btn-admin-danger" style="padding:.3em .6em; font-size:.76rem;" data-delete-cat="${cat.id}">Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function initAddCategoryModal() {
    const saveBtn = document.getElementById("saveNewCategoryBtn");
    if (!saveBtn) return;

    saveBtn.addEventListener("click", async function() {
      const name = document.getElementById("newCatName").value.trim();
      const slug = document.getElementById("newCatSlug").value.trim().toLowerCase();
      const desc = document.getElementById("newCatDesc").value.trim();
      const img = document.getElementById("newCatImagePreset").value;
      const status = document.getElementById("newCatStatus").value;

      if (!name || !slug) {
        if (window.Toast) window.Toast.show("Please enter category name and slug.");
        return;
      }

      const payload = {
        name: name,
        slug: slug,
        description: desc,
        image_url: img,
        is_active: status === "Active"
      };

      if (window.AdminAPI && window.AdminAPI.createCategory) {
        await window.AdminAPI.createCategory(payload);
        await loadCategoriesFromAPI();
      } else {
        const newCat = {
          id: "cat_" + Date.now().toString(36),
          name: name,
          slug: slug,
          description: desc,
          image: img,
          status: status,
          productCount: 0
        };
        categories.push(newCat);
        saveCategories();
        renderCategoriesTable();
      }

      if (window.Modal) window.Modal.close("addCategoryModal");
      if (window.Toast) window.Toast.show("New category added!");
    });
  }

  let editCategoryImages = [];

  function renderEditCategoryPreviews() {
    const previewWrap = document.getElementById("editCatImagePreviews");
    if (!previewWrap) return;
    if (editCategoryImages.length === 0) {
      previewWrap.innerHTML = `<span style="font-size:.76rem; color:var(--admin-ink-soft);">No custom browse images loaded.</span>`;
      return;
    }
    previewWrap.innerHTML = editCategoryImages.map(function(src, i) {
      return `
        <div style="width:50px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; border:1px solid var(--admin-border); position:relative;">
          <img src="${src}" style="width:100%; height:100%; object-fit:cover;">
          <span style="position:absolute; bottom:0; left:0; right:0; background:rgba(0,0,0,.6); color:#fff; font-size:.65rem; text-align:center;">${i + 1}</span>
        </div>
      `;
    }).join("");
  }

  function initEditCategoryModal() {
    const fileInput = document.getElementById("editCatImageFiles");
    if (fileInput) {
      fileInput.addEventListener("change", async function() {
        if (!fileInput.files || !fileInput.files.length) return;
        editCategoryImages = [];
        const file = fileInput.files[0];
        if (file && window.AdminAPI && window.AdminAPI.uploadImage) {
          const uploadRes = await window.AdminAPI.uploadImage(file);
          if (uploadRes.success && uploadRes.data && uploadRes.data.url) {
            editCategoryImages.push(uploadRes.data.url);
            renderEditCategoryPreviews();
            if (window.Toast) window.Toast.show(`Category image uploaded!`);
            return;
          }
        }
        let loaded = 0;
        Array.from(fileInput.files).forEach(function(f) {
          const reader = new FileReader();
          reader.onload = function(evt) {
            editCategoryImages.push(evt.target.result);
            loaded += 1;
            if (loaded === fileInput.files.length) {
              renderEditCategoryPreviews();
              if (window.Toast) window.Toast.show(`${loaded} category images loaded!`);
            }
          };
          reader.readAsDataURL(f);
        });
      });
    }

    const updateBtn = document.getElementById("updateCategoryBtn");
    if (!updateBtn) return;

    updateBtn.addEventListener("click", async function() {
      if (!editingCategoryId) return;

      const cat = categories.find(function(c) { return String(c.id) === String(editingCategoryId); });
      if (cat) {
        const name = document.getElementById("editCatName").value.trim();
        const slug = document.getElementById("editCatSlug").value.trim().toLowerCase();
        const desc = document.getElementById("editCatDesc").value.trim();
        let image = document.getElementById("editCatImagePreset").value;
        if (editCategoryImages.length > 0) {
          image = editCategoryImages[0];
        }
        const status = document.getElementById("editCatStatus").value;

        const payload = {
          name: name,
          slug: slug,
          description: desc,
          image_url: image,
          is_active: status === "Active"
        };

        if (window.AdminAPI && window.AdminAPI.updateCategory) {
          await window.AdminAPI.updateCategory(editingCategoryId, payload);
          await loadCategoriesFromAPI();
        } else {
          cat.name = name;
          cat.slug = slug;
          cat.description = desc;
          cat.image = image;
          cat.status = status;
          saveCategories();
          renderCategoriesTable();
        }

        if (window.Modal) window.Modal.close("editCategoryModal");
        if (window.Toast) window.Toast.show("Category updated!");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    loadCategoriesFromAPI();
    renderCategoriesTable();
    initAddCategoryModal();
    initEditCategoryModal();

    const addBtn = document.getElementById("addCategoryModalBtn");
    if (addBtn) {
      addBtn.addEventListener("click", function() {
        if (window.Modal) window.Modal.open("addCategoryModal");
      });
    }

    const tableBody = document.getElementById("adminCategoriesTableBody");
    if (tableBody) {
      tableBody.addEventListener("click", async function(e) {
        const toggleBtn = e.target.closest("[data-toggle-status]");
        const editBtn = e.target.closest("[data-edit-cat]");
        const deleteBtn = e.target.closest("[data-delete-cat]");

        if (toggleBtn) {
          const id = toggleBtn.dataset.toggleStatus;
          const cat = categories.find(function(c) { return String(c.id) === String(id); });
          if (cat) {
            const newIsActive = cat.status !== "Active";
            if (window.AdminAPI && window.AdminAPI.updateCategory) {
              await window.AdminAPI.updateCategory(id, { is_active: newIsActive });
              await loadCategoriesFromAPI();
            } else {
              cat.status = newIsActive ? "Active" : "Inactive";
              saveCategories();
              renderCategoriesTable();
            }
            if (window.Toast) window.Toast.show(`Category status updated`);
          }
        }

        if (editBtn) {
          editingCategoryId = editBtn.dataset.editCat;
          const cat = categories.find(function(c) { return String(c.id) === String(editingCategoryId); });
          if (cat) {
            document.getElementById("editCatName").value = cat.name;
            document.getElementById("editCatSlug").value = cat.slug;
            document.getElementById("editCatDesc").value = cat.description || "";
            document.getElementById("editCatImagePreset").value = cat.image || "";
            document.getElementById("editCatStatus").value = cat.status || "Active";
            if (window.Modal) window.Modal.open("editCategoryModal");
          }
        }

        if (deleteBtn) {
          pendingDeleteId = deleteBtn.dataset.deleteCat;
          if (window.Modal) window.Modal.open("adminConfirmModal");
        }
      });
    }

    const confirmActionBtn = document.getElementById("adminConfirmModalActionBtn");
    if (confirmActionBtn) {
      confirmActionBtn.addEventListener("click", async function() {
        if (pendingDeleteId) {
          if (window.AdminAPI && window.AdminAPI.deleteCategory) {
            await window.AdminAPI.deleteCategory(pendingDeleteId);
            await loadCategoriesFromAPI();
          } else {
            categories = categories.filter(function(c) { return String(c.id) !== String(pendingDeleteId); });
            saveCategories();
            renderCategoriesTable();
          }
          if (window.Modal) window.Modal.close("adminConfirmModal");
          if (window.Toast) window.Toast.show("Category deleted.");
          pendingDeleteId = null;
        }
      });
    }
  });
})();
