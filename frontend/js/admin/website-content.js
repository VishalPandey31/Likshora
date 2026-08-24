/* =========================================================
   LIKSHORA — Admin Website Content Controller
   Homepage banners, hero slider CRUD, rotating models CRUD & REST API integration
   ========================================================= */

(function() {
  const SITE_CONTENT_KEY = "rv_site_content";

  const DEFAULT_CONTENT = {
    heroTitle: "Kurtas, coloured for everyday wear.",
    heroSubtitle: "Handcrafted cotton kurtas, tunic sets, and breezy co-ords designed for effortless modern lifestyle.",
    heroCtaText: "Explore Collection",
    announcementText: "Complimentary shipping on prepaid orders, across India",
    announcementActive: true,
    contactEmail: "care@LIKSHORA.com",
    contactPhone: "+91 9876543210",
    studioAddress: "LIKSHORA Design Studio, Indiranagar 100ft Road, Bengaluru, KA 560038",
    footerBrandBio: "Kurtas, coloured for everyday wear.",
    copyrightText: "© 2026 Likshora. All rights reserved.",
    heroSlides: [
      { id: "slide_1", caption: "LIKSHORA model wearing kurta with embroidered stole", image: "../../assets/images/products/model-photo-1.jpg" },
      { id: "slide_2", caption: "LIKSHORA model in courtyard wearing kurta with embroidered stole", image: "../../assets/images/products/model-photo-2.jpg" },
      { id: "slide_3", caption: "LIKSHORA model leaning against pillar wearing kurta with stole", image: "../../assets/images/products/model-photo-4.jpg" },
      { id: "slide_4", caption: "LIKSHORA model wearing white kurta outdoors", image: "../../assets/images/products/model-photo-7.jpg" }
    ],
    rotatingModels: [
      { id: "mod_1", name: "Model photo 1", image: "../../assets/images/products/model-photo-1.jpg" },
      { id: "mod_2", name: "Model photo 2", image: "../../assets/images/products/model-photo-2.jpg" },
      { id: "mod_3", name: "Model photo 3", image: "../../assets/images/products/model-photo-3.jpg" },
      { id: "mod_4", name: "Model photo 4", image: "../../assets/images/products/model-photo-4.jpg" },
      { id: "mod_5", name: "Model photo 6", image: "../../assets/images/products/model-photo-6.jpg" },
      { id: "mod_6", name: "Model photo 7", image: "../../assets/images/products/model-photo-7.jpg" }
    ]
  };

  let content = window.StorageUtils ? window.StorageUtils.readJSON(SITE_CONTENT_KEY, DEFAULT_CONTENT) : DEFAULT_CONTENT;

  async function loadContentFromAPI() {
    if (window.AdminAPI && window.AdminAPI.getSiteContent) {
      try {
        const res = await window.AdminAPI.getSiteContent();
        if (res.success && res.data) {
          content = Object.assign({}, DEFAULT_CONTENT, res.data);
          if (window.StorageUtils) {
            window.StorageUtils.writeJSON(SITE_CONTENT_KEY, content);
          }
          populateFormFields();
        }
      } catch (err) {
        console.warn("Could not fetch site content from REST API:", err);
      }
    }
  }

  function populateFormFields() {
    const heroTitleInput = document.getElementById("contentHeroTitle");
    const heroSubtitleInput = document.getElementById("contentHeroSubtitle");
    const heroCtaInput = document.getElementById("contentHeroCta");
    const announceTextInput = document.getElementById("contentAnnounceText");
    const announceToggleInput = document.getElementById("contentAnnounceToggle");
    const emailInput = document.getElementById("contentContactEmail");
    const phoneInput = document.getElementById("contentContactPhone");
    const addressInput = document.getElementById("contentStudioAddress");
    const footerBioInput = document.getElementById("contentFooterBio");
    const copyrightInput = document.getElementById("contentCopyright");

    if (heroTitleInput) heroTitleInput.value = content.heroTitle || "";
    if (heroSubtitleInput) heroSubtitleInput.value = content.heroSubtitle || "";
    if (heroCtaInput) heroCtaInput.value = content.heroCtaText || "";
    if (announceTextInput) announceTextInput.value = content.announcementText || "";
    if (announceToggleInput) announceToggleInput.checked = content.announcementActive !== false;
    if (emailInput) emailInput.value = content.contactEmail || "";
    if (phoneInput) phoneInput.value = content.contactPhone || "";
    if (addressInput) addressInput.value = content.studioAddress || "";
    if (footerBioInput) footerBioInput.value = content.footerBrandBio || "";
    if (copyrightInput) copyrightInput.value = content.copyrightText || "";

    renderHeroSlidesAdmin();
    renderRotatingModelsAdmin();
  }

  function renderHeroSlidesAdmin() {
    const wrap = document.getElementById("heroSlidesAdminList");
    if (!wrap) return;

    if (!content.heroSlides || content.heroSlides.length === 0) {
      wrap.innerHTML = `<p style="font-size:.84rem; color:var(--admin-ink-soft); margin:0;">No slides available. Click "+ Add New Slide" above.</p>`;
      return;
    }

    wrap.innerHTML = content.heroSlides.map(function(slide, idx) {
      let src = slide.image;
      if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) {
        src = "../../" + src;
      }
      return `
        <div style="display:flex; gap:1em; align-items:center; background:var(--white); border:1px solid var(--admin-border); padding:.8em; border-radius:var(--radius-sm);" data-slide-idx="${idx}">
          <div style="width:60px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
            <img src="${src}" style="width:100%; height:100%; object-fit:cover;">
          </div>
          <div style="flex:1;">
            <label style="font-size:.78rem; font-weight:600; color:var(--admin-ink-soft); display:block; margin-bottom:.3em;">Slide ${idx + 1} Caption / Alt Text</label>
            <input type="text" class="auth-input slide-caption-input" data-idx="${idx}" value="${window.Formatters ? window.Formatters.escapeHTML(slide.caption || '') : (slide.caption || '')}" style="font-size:.84rem;">
            <div style="display:flex; gap:.6em; align-items:center; margin-top:.4em;">
              <label class="btn-admin-secondary" style="font-size:.72rem; padding:.2em .6em; cursor:pointer;">
                📁 Browse &amp; Replace Image
                <input type="file" class="slide-file-input" accept="image/*" style="display:none;" data-idx="${idx}">
              </label>
              <button type="button" class="btn-admin-secondary preview-slide-btn" style="font-size:.72rem; padding:.2em .6em;" data-idx="${idx}">🔍 Preview</button>
            </div>
          </div>
          <button type="button" class="btn-admin-danger delete-slide-btn" data-idx="${idx}" style="padding:.4em .8em; font-size:.78rem;">✕ Delete</button>
        </div>
      `;
    }).join("");
  }

  function renderRotatingModelsAdmin() {
    const wrap = document.getElementById("rotatingModelsAdminList");
    if (!wrap) return;

    if (!content.rotatingModels || content.rotatingModels.length === 0) {
      wrap.innerHTML = `<p style="font-size:.84rem; color:var(--admin-ink-soft); margin:0;">No model photos added. Click "+ Add Model Photo" above.</p>`;
      return;
    }

    wrap.innerHTML = content.rotatingModels.map(function(mod, idx) {
      let src = mod.image;
      if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) {
        src = "../../" + src;
      }
      return `
        <div style="display:flex; gap:1em; align-items:center; background:var(--white); border:1px solid var(--admin-border); padding:.8em; border-radius:var(--radius-sm);" data-model-idx="${idx}">
          <div style="width:50px; aspect-ratio:3/4; border-radius:4px; overflow:hidden; background:var(--sand-deep); flex-shrink:0;">
            <img src="${src}" style="width:100%; height:100%; object-fit:cover;">
          </div>
          <div style="flex:1;">
            <label style="font-size:.78rem; font-weight:600; color:var(--admin-ink-soft); display:block; margin-bottom:.3em;">Model Name / Tag</label>
            <input type="text" class="auth-input model-name-input" data-idx="${idx}" value="${window.Formatters ? window.Formatters.escapeHTML(mod.name || '') : (mod.name || '')}" style="font-size:.84rem;">
            <div style="display:flex; gap:.6em; align-items:center; margin-top:.4em;">
              <label class="btn-admin-secondary" style="font-size:.72rem; padding:.2em .6em; cursor:pointer;">
                📁 Browse &amp; Replace Image
                <input type="file" class="model-file-input" accept="image/*" style="display:none;" data-idx="${idx}">
              </label>
              <button type="button" class="btn-admin-secondary preview-model-btn" style="font-size:.72rem; padding:.2em .6em;" data-idx="${idx}">🔍 Preview</button>
            </div>
          </div>
          <button type="button" class="btn-admin-danger delete-model-btn" data-idx="${idx}" style="padding:.4em .8em; font-size:.78rem;">✕ Delete</button>
        </div>
      `;
    }).join("");
  }

  function initSlidersAndModelsEvents() {
    const addSlideBtn = document.getElementById("addHeroSlideBtn");
    if (addSlideBtn) {
      addSlideBtn.addEventListener("click", function() {
        if (!content.heroSlides) content.heroSlides = [];
        content.heroSlides.push({
          id: "slide_" + Date.now(),
          caption: "New Hero Slide",
          image: "../../assets/images/products/model-photo-1.jpg"
        });
        renderHeroSlidesAdmin();
        if (window.Toast) window.Toast.show("New hero slide added!");
      });
    }

    const addModelBtn = document.getElementById("addModelPhotoBtn");
    if (addModelBtn) {
      addModelBtn.addEventListener("click", function() {
        if (!content.rotatingModels) content.rotatingModels = [];
        content.rotatingModels.push({
          id: "mod_" + Date.now(),
          name: "New Model Photo",
          image: "../../assets/images/products/model-photo-2.jpg"
        });
        renderRotatingModelsAdmin();
        if (window.Toast) window.Toast.show("New model photo added!");
      });
    }

    const slidesList = document.getElementById("heroSlidesAdminList");
    if (slidesList) {
      slidesList.addEventListener("click", function(e) {
        const deleteBtn = e.target.closest(".delete-slide-btn");
        const previewBtn = e.target.closest(".preview-slide-btn");

        if (deleteBtn) {
          const idx = parseInt(deleteBtn.dataset.idx, 10);
          content.heroSlides.splice(idx, 1);
          renderHeroSlidesAdmin();
          if (window.Toast) window.Toast.show("Slide deleted");
        }

        if (previewBtn) {
          const idx = parseInt(previewBtn.dataset.idx, 10);
          const slide = content.heroSlides[idx];
          if (slide && window.Toast) {
            window.Toast.show("Previewing Slide: " + (slide.caption || 'Hero Slide'));
            let src = slide.image;
            if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) src = "../../" + src;
            window.open(src, '_blank');
          }
        }
      });

      slidesList.addEventListener("change", async function(e) {
        const fileInput = e.target.closest(".slide-file-input");
        const captionInput = e.target.closest(".slide-caption-input");

        if (captionInput) {
          const idx = parseInt(captionInput.dataset.idx, 10);
          if (content.heroSlides[idx]) {
            content.heroSlides[idx].caption = captionInput.value.trim();
          }
        }

        if (fileInput && fileInput.files && fileInput.files[0]) {
          const idx = parseInt(fileInput.dataset.idx, 10);
          const file = fileInput.files[0];
          if (window.AdminAPI && window.AdminAPI.uploadImage) {
            const uploadRes = await window.AdminAPI.uploadImage(file);
            if (uploadRes.success && uploadRes.data && uploadRes.data.url) {
              if (content.heroSlides[idx]) {
                content.heroSlides[idx].image = uploadRes.data.url;
                renderHeroSlidesAdmin();
                if (window.Toast) window.Toast.show("Hero slide image uploaded!");
                return;
              }
            }
          }
          const reader = new FileReader();
          reader.onload = function(evt) {
            if (content.heroSlides[idx]) {
              content.heroSlides[idx].image = evt.target.result;
              renderHeroSlidesAdmin();
              if (window.Toast) window.Toast.show("Hero slide image replaced!");
            }
          };
          reader.readAsDataURL(file);
        }
      });
    }

    const modelsList = document.getElementById("rotatingModelsAdminList");
    if (modelsList) {
      modelsList.addEventListener("click", function(e) {
        const deleteBtn = e.target.closest(".delete-model-btn");
        const previewBtn = e.target.closest(".preview-model-btn");

        if (deleteBtn) {
          const idx = parseInt(deleteBtn.dataset.idx, 10);
          content.rotatingModels.splice(idx, 1);
          renderRotatingModelsAdmin();
          if (window.Toast) window.Toast.show("Model photo deleted");
        }

        if (previewBtn) {
          const idx = parseInt(previewBtn.dataset.idx, 10);
          const mod = content.rotatingModels[idx];
          if (mod && window.Toast) {
            window.Toast.show("Previewing Model: " + (mod.name || 'Model Photo'));
            let src = mod.image;
            if (src && !src.startsWith("http") && !src.startsWith("data:") && !src.startsWith("../")) src = "../../" + src;
            window.open(src, '_blank');
          }
        }
      });

      modelsList.addEventListener("change", async function(e) {
        const fileInput = e.target.closest(".model-file-input");
        const nameInput = e.target.closest(".model-name-input");

        if (nameInput) {
          const idx = parseInt(nameInput.dataset.idx, 10);
          if (content.rotatingModels[idx]) {
            content.rotatingModels[idx].name = nameInput.value.trim();
          }
        }

        if (fileInput && fileInput.files && fileInput.files[0]) {
          const idx = parseInt(fileInput.dataset.idx, 10);
          const file = fileInput.files[0];
          if (window.AdminAPI && window.AdminAPI.uploadImage) {
            const uploadRes = await window.AdminAPI.uploadImage(file);
            if (uploadRes.success && uploadRes.data && uploadRes.data.url) {
              if (content.rotatingModels[idx]) {
                content.rotatingModels[idx].image = uploadRes.data.url;
                renderRotatingModelsAdmin();
                if (window.Toast) window.Toast.show("Model photo uploaded!");
                return;
              }
            }
          }
          const reader = new FileReader();
          reader.onload = function(evt) {
            if (content.rotatingModels[idx]) {
              content.rotatingModels[idx].image = evt.target.result;
              renderRotatingModelsAdmin();
              if (window.Toast) window.Toast.show("Model photo replaced!");
            }
          };
          reader.readAsDataURL(file);
        }
      });
    }
  }

  function initContentSaveForm() {
    const form = document.getElementById("websiteContentForm");
    if (!form) return;

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      content.heroTitle = document.getElementById("contentHeroTitle").value.trim();
      content.heroSubtitle = document.getElementById("contentHeroSubtitle").value.trim();
      content.heroCtaText = document.getElementById("contentHeroCta").value.trim();
      content.announcementText = document.getElementById("contentAnnounceText").value.trim();
      content.announcementActive = document.getElementById("contentAnnounceToggle").checked;
      content.contactEmail = document.getElementById("contentContactEmail").value.trim();
      content.contactPhone = document.getElementById("contentContactPhone").value.trim();
      content.studioAddress = document.getElementById("contentStudioAddress").value.trim();
      content.footerBrandBio = document.getElementById("contentFooterBio").value.trim();
      content.copyrightText = document.getElementById("contentCopyright").value.trim();

      if (window.AdminAPI && window.AdminAPI.updateSiteContent) {
        try {
          await window.AdminAPI.updateSiteContent(content);
        } catch (err) {
          console.warn("Could not save site content to API:", err);
        }
      }

      if (window.StorageUtils) {
        window.StorageUtils.writeJSON(SITE_CONTENT_KEY, content);
      }

      if (window.Toast) window.Toast.show("Website content configuration saved successfully!");
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    loadContentFromAPI();
    populateFormFields();
    initSlidersAndModelsEvents();
    initContentSaveForm();
  });
})();
