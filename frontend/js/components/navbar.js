/* =========================================================
   LIKSHORA — Navbar Component Controller
   Header navigation, mobile menu, search & cart badges
   ========================================================= */

window.NavbarComponent = (function() {
  function initHeaderControls() {
    // Menu toggle for mobile
    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");
    if (menuToggle && mainNav) {
      menuToggle.addEventListener("click", function() {
        mainNav.classList.toggle("open");
        menuToggle.classList.toggle("open");
      });
    }

    // Search Toggle
    const searchToggle = document.getElementById("searchToggle");
    const searchClose = document.getElementById("searchClose");
    const searchPanel = document.getElementById("searchPanel");
    const searchInput = document.getElementById("searchInput");

    if (searchToggle && searchPanel) {
      searchToggle.addEventListener("click", function() {
        if (searchPanel.classList.contains("open")) {
          closeSearch();
        } else {
          openSearch();
        }
      });
    }

    if (searchClose) {
      searchClose.addEventListener("click", closeSearch);
    }

    if (searchInput) {
      searchInput.addEventListener("input", function(e) {
        if (window.renderSearchResults) {
          window.renderSearchResults(e.target.value);
        }
      });
    }
    // About & Story Modal Triggers
    function ensureAboutModal() {
      let overlay = document.getElementById("aboutOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "aboutOverlay";
        overlay.innerHTML = `
  <div class="modal modal-about">
    <button class="icon-btn modal-close" id="aboutClose">&times;</button>
    <p class="eyebrow">ABOUT</p>
    <h3>About LIKSHORA</h3>
    <div class="about-editable" id="aboutContent">
      <p class="about-lead">It started with a simple thought.</p>

      <p>Honestly, Likshora is not just a clothing brand.<br>
      It’s an idea.</p>

      <p>An idea to bring the beauty of Indian tradition into the world of modern fashion — without losing what makes it special.</p>

      <p>I have always believed that Indian clothing carries something beyond fabric and design. It carries stories, emotions, culture, and a sense of identity. But as lifestyles changed and fashion became more fast-paced, I felt there was a gap between traditional elegance and modern everyday fashion.</p>

      <p>That gap became the reason Likshora was born.</p>

      <p>I wanted to create something that feels traditional at heart, but modern in the way it looks, feels and fits into everyday life.</p>

      <p>Something you could wear to a family gathering, a festive occasion, a day at work, or simply when you want to feel a little more connected to your roots.</p>

      <p>And that's where our journey began.</p>

      <h4 class="about-subtitle">More than just clothes.</h4>

      <p>At Likshora, we don't look at a Kurti as just another piece of clothing.</p>

      <p>For us, it is a way of expressing who you are.</p>

      <p>Every design begins with an intention — to keep the essence of Indian aesthetics alive while giving it a fresh, contemporary identity.</p>

      <p>We pay attention to the little things:<br>
      the silhouette, the fabric, the colours, the detailing, the comfort and the overall feel.</p>

      <p>Because we believe that when something is made with thought, you can feel it when you wear it.</p>

      <h4 class="about-subtitle">Tradition, but with a new perspective.</h4>

      <p>We don't believe tradition belongs only to the past.</p>

      <p>Tradition can evolve.<br>
      It can change with generations.<br>
      It can take new forms without losing its soul.</p>

      <p>That's what Likshora stands for.</p>

      <p>We take inspiration from the colours, craftsmanship, silhouettes and emotions that have been a part of Indian fashion for generations — and reinterpret them for the woman of today.</p>

      <p>A woman who loves her roots, but also has her own identity.</p>

      <p>A woman who doesn't dress to follow a trend, but dresses to express herself.</p>

      <h4 class="about-subtitle">Built with a vision.</h4>

      <p>Likshora started with a small idea and a big belief — that Indian fashion deserves to feel just as effortless, contemporary and exciting as anything else in the fashion world.</p>

      <p>There is still so much beauty in our culture waiting to be reimagined.</p>

      <p>And we want to be a part of that journey.</p>

      <p>From the first sketch to the final stitch, we are building Likshora with patience, curiosity and a constant desire to do better.</p>

      <p>We may be starting small, but our vision is much bigger.</p>

      <p>We want Likshora to become a brand that people don't just recognize for its clothes, but remember for how those clothes make them feel.</p>

      <h4 class="about-subtitle">This is just the beginning.</h4>

      <p>Likshora is still at the beginning of its journey.</p>

      <p>But every design, every order and every person who chooses to wear us becomes a part of our story.</p>

      <p>And if there is one thing we want to create through Likshora, it is this feeling:</p>

      <p class="about-quote">You don't have to choose between tradition and modernity.<br>
      You can carry both.</p>

      <p>Because tradition doesn't need to be left behind.</p>

      <p>It just needs a new way to be worn.</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    function ensureStoryModal() {
      let overlay = document.getElementById("storyOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "storyOverlay";
        overlay.innerHTML = `
  <div class="modal modal-story">
    <button class="icon-btn modal-close" id="storyClose">&times;</button>
    <p class="eyebrow">OUR STORY</p>
    <h3>Our Story</h3>
    <div class="about-editable" id="storyContent">
      <p class="about-lead">It started with a simple thought.</p>

      <p>Honestly, Likshora is not just a clothing brand.<br>
      It’s an idea.</p>

      <p>An idea to bring the beauty of Indian tradition into the world of modern fashion — without losing what makes it special.</p>

      <p>I have always believed that Indian clothing carries something beyond fabric and design. It carries stories, emotions, culture, and a sense of identity. But as lifestyles changed and fashion became more fast-paced, I felt there was a gap between traditional elegance and modern everyday fashion.</p>

      <p>That gap became the reason Likshora was born.</p>

      <p>I wanted to create something that feels traditional at heart, but modern in the way it looks, feels and fits into everyday life.</p>

      <p>Something you could wear to a family gathering, a festive occasion, a day at work, or simply when you want to feel a little more connected to your roots.</p>

      <p>And that's where our journey began.</p>

      <h4 class="about-subtitle">More than just clothes.</h4>

      <p>At Likshora, we don't look at a Kurti as just another piece of clothing.</p>

      <p>For us, it is a way of expressing who you are.</p>

      <p>Every design begins with an intention — to keep the essence of Indian aesthetics alive while giving it a fresh, contemporary identity.</p>

      <p>We pay attention to the little things:<br>
      the silhouette, the fabric, the colours, the detailing, the comfort and the overall feel.</p>

      <p>Because we believe that when something is made with thought, you can feel it when you wear it.</p>

      <h4 class="about-subtitle">Tradition, but with a new perspective.</h4>

      <p>We don't believe tradition belongs only to the past.</p>

      <p>Tradition can evolve.<br>
      It can change with generations.<br>
      It can take new forms without losing its soul.</p>

      <p>That's what Likshora stands for.</p>

      <p>We take inspiration from the colours, craftsmanship, silhouettes and emotions that have been a part of Indian fashion for generations — and reinterpret them for the woman of today.</p>

      <p>A woman who loves her roots, but also has her own identity.</p>

      <p>A woman who doesn't dress to follow a trend, but dresses to express herself.</p>

      <h4 class="about-subtitle">Built with a vision.</h4>

      <p>Likshora started with a small idea and a big belief — that Indian fashion deserves to feel just as effortless, contemporary and exciting as anything else in the fashion world.</p>

      <p>There is still so much beauty in our culture waiting to be reimagined.</p>

      <p>And we want to be a part of that journey.</p>

      <p>From the first sketch to the final stitch, we are building Likshora with patience, curiosity and a constant desire to do better.</p>

      <p>We may be starting small, but our vision is much bigger.</p>

      <p>We want Likshora to become a brand that people don't just recognize for its clothes, but remember for how those clothes make them feel.</p>

      <h4 class="about-subtitle">This is just the beginning.</h4>

      <p>Likshora is still at the beginning of its journey.</p>

      <p>But every design, every order and every person who chooses to wear us becomes a part of our story.</p>

      <p>And if there is one thing we want to create through Likshora, it is this feeling:</p>

      <p class="about-quote">You don't have to choose between tradition and modernity.<br>
      You can carry both.</p>

      <p>Because tradition doesn't need to be left behind.</p>

      <p>It just needs a new way to be worn.</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    function ensureSustainabilityModal() {
      let overlay = document.getElementById("sustainabilityOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "sustainabilityOverlay";
        overlay.innerHTML = `
  <div class="modal modal-sustainability">
    <button class="icon-btn modal-close" id="sustainabilityClose">&times;</button>
    <p class="eyebrow">SUSTAINABILITY</p>
    <h3>Sustainability</h3>
    <div class="about-editable" id="sustainabilityContent">
      <p class="about-lead">At Likshora, we believe that creating beautiful clothing should also mean being thoughtful about how it is created.</p>

      <p>Our approach to sustainability begins with making conscious choices at every stage of our journey — from the fabrics we explore to the way our products are made, packaged and delivered.</p>

      <h4 class="about-subtitle">Thoughtful Production</h4>

      <p>We believe in creating with purpose rather than simply creating more.</p>

      <p>Our collections are developed thoughtfully, with attention to design, quality and usability. We aim to avoid unnecessary production and focus on pieces that can remain a part of your wardrobe beyond a single season.</p>

      <h4 class="about-subtitle">Quality Over Quantity</h4>

      <p>For us, sustainability also means creating products that are made to be worn, loved and cared for.</p>

      <p>We focus on comfortable fabrics, thoughtful designs and quality finishing so that our pieces can become long-term favourites rather than short-lived trends.</p>

      <h4 class="about-subtitle">Conscious Packaging</h4>

      <p>We are continuously exploring ways to make our packaging more thoughtful and responsible.</p>

      <p>Wherever possible, we aim to reduce unnecessary packaging and choose materials that can be reused or recycled.</p>

      <h4 class="about-subtitle">A Journey, Not a Claim</h4>

      <p>We know that sustainability is not something a brand can achieve overnight.</p>

      <p>We are still learning, improving and finding better ways to reduce our impact.</p>

      <p>Every small improvement matters.</p>

      <p>As Likshora grows, our commitment is to grow responsibly with it.</p>

      <p class="about-quote">Because fashion should not only look good.<br>
      It should feel good to make better choices.</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    function ensureCareersModal() {
      let overlay = document.getElementById("careersOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "careersOverlay";
        overlay.innerHTML = `
  <div class="modal modal-careers">
    <button class="icon-btn modal-close" id="careersClose">&times;</button>
    <p class="eyebrow">CAREERS</p>
    <h3>Careers</h3>
    <div class="about-editable" id="careersContent">
      <p class="about-lead">Build something meaningful with us.</p>

      <p>Likshora is a young brand with a big vision.</p>

      <p>We are building a modern Indian fashion brand that brings together tradition, creativity and contemporary design — and we are looking for people who want to be a part of that journey.</p>

      <p>At Likshora, we believe great ideas can come from anywhere.</p>

      <p>Whether you are passionate about fashion, design, photography, content, marketing, social media, operations or customer experience, there may be a place for you here.</p>

      <h4 class="about-subtitle">What we value</h4>

      <p><strong>Creativity</strong><br>
      We love people who think differently and aren't afraid to bring new ideas.</p>

      <p><strong>Ownership</strong><br>
      We believe in taking responsibility and seeing things through.</p>

      <p><strong>Curiosity</strong><br>
      We are constantly learning, experimenting and improving.</p>

      <p><strong>Attention to Detail</strong><br>
      Small details can make a big difference — especially in fashion.</p>

      <p><strong>Respect</strong><br>
      We believe in building a workplace where everyone is heard and valued.</p>

      <h4 class="about-subtitle">Grow with Likshora</h4>

      <p>We are at the beginning of our journey, which means there is a lot to build.</p>

      <p>If you want to work in an environment where your ideas can actually make an impact, we'd love to hear from you.</p>

      <h4 class="about-subtitle">Think you belong at Likshora?</h4>

      <p>Send us your profile, portfolio or simply tell us what you could bring to the brand.</p>

      <p class="about-quote">Email: <a href="mailto:support@likshora.com" style="color:inherit; text-decoration:underline;">support@likshora.com</a><br>
      Subject: Career Opportunity — Likshora</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    function ensurePrivacyModal() {
      let overlay = document.getElementById("privacyOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "privacyOverlay";
        overlay.innerHTML = `
  <div class="modal modal-privacy">
    <button class="icon-btn modal-close" id="privacyClose">&times;</button>
    <p class="eyebrow">LEGAL</p>
    <h3>Privacy Policy</h3>
    <div class="about-editable" id="privacyContent">
      <p class="about-lead">Effective Date: 22 August 2026</p>

      <p>At Likshora, we respect your privacy and are committed to protecting the personal information you share with us.</p>

      <p>This Privacy Policy explains what information we collect, how we use it and how we protect it when you use our website or purchase our products.</p>

      <h4 class="about-subtitle">1. Information We Collect</h4>
      <p>When you visit or use our website, place an order, create an account or contact us, we may collect information such as:<br>
      • Name<br>
      • Email address<br>
      • Mobile number<br>
      • Billing and shipping address<br>
      • Order and transaction details<br>
      • Account login information<br>
      • Information you provide when contacting customer support</p>

      <p>We may also collect certain technical information such as your IP address, browser type, device information and website usage information.</p>

      <h4 class="about-subtitle">2. How We Use Your Information</h4>
      <p>We may use your information to:<br>
      • Process and deliver your orders<br>
      • Provide order confirmations and tracking updates<br>
      • Communicate with you regarding your purchases<br>
      • Provide customer support<br>
      • Improve our website, products and services<br>
      • Prevent fraud, misuse or unauthorized activity<br>
      • Comply with applicable legal requirements<br>
      • Send promotional communication where permitted and where you have provided appropriate consent</p>

      <h4 class="about-subtitle">3. Payment Information</h4>
      <p>Payments may be processed through third-party payment service providers.</p>
      <p>Likshora does not intentionally store complete credit or debit card information on its own servers. Payment information is handled by the relevant payment service provider according to its security and privacy practices.</p>

      <h4 class="about-subtitle">4. Cookies</h4>
      <p>Our website may use cookies and similar technologies to improve your browsing experience, understand website usage and remember certain preferences.</p>
      <p>You may be able to control cookies through your browser settings.</p>

      <h4 class="about-subtitle">5. Sharing of Information</h4>
      <p>We do not sell your personal information.</p>
      <p>We may share necessary information with trusted service providers who help us operate our business, such as:<br>
      • Payment providers<br>
      • Courier and logistics partners<br>
      • Website and technology service providers<br>
      • Customer support providers</p>
      <p>Such information is shared only when reasonably necessary to provide our services or comply with legal obligations.</p>

      <h4 class="about-subtitle">6. Data Security</h4>
      <p>We take reasonable technical and organizational measures to protect your information from unauthorized access, misuse, alteration or disclosure.</p>
      <p>However, no method of transmission or electronic storage can be guaranteed to be completely secure.</p>

      <h4 class="about-subtitle">7. Your Rights</h4>
      <p>Depending on applicable law, you may have rights regarding your personal information, including requesting access, correction or deletion of certain information.</p>
      <p>To make a privacy-related request, contact us using the details below.</p>

      <h4 class="about-subtitle">8. Children's Privacy</h4>
      <p>Our website is not intended for individuals who are not legally permitted to use online shopping services under applicable law.</p>
      <p>We do not knowingly collect personal information from children without appropriate authorization.</p>

      <h4 class="about-subtitle">9. Changes to This Policy</h4>
      <p>We may update this Privacy Policy from time to time.</p>
      <p>Any changes will be published on this page with an updated effective date.</p>

      <h4 class="about-subtitle">10. Contact Us</h4>
      <p>For questions or requests relating to this Privacy Policy:</p>
      <p class="about-quote">Email: <a href="mailto:support@likshora.com" style="color:inherit; text-decoration:underline;">support@likshora.com</a><br>
      Support Hours: Monday to Saturday, 10:00 AM – 6:00 PM (IST)<br>
      Address: Flat No. 401/402, Building No. 7B, Sector 2, Roop Rajat, Maan, Boisar East, Maharashtra, India.</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    function ensureTermsModal() {
      let overlay = document.getElementById("termsOverlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "termsOverlay";
        overlay.innerHTML = `
  <div class="modal modal-terms">
    <button class="icon-btn modal-close" id="termsClose">&times;</button>
    <p class="eyebrow">LEGAL</p>
    <h3>Terms of Service</h3>
    <div class="about-editable" id="termsContent">
      <p class="about-lead">Effective Date: 22 August 2026</p>

      <p>Welcome to Likshora.<br>
      By accessing or using our website, you agree to these Terms of Service. Please read them carefully before using our website or placing an order.</p>

      <h4 class="about-subtitle">1. About Likshora</h4>
      <p>Likshora is a fashion brand offering clothing and related products through its online platform.</p>
      <p>These Terms govern your use of our website and your purchase of products from us.</p>

      <h4 class="about-subtitle">2. Your Account</h4>
      <p>If you create an account, you are responsible for maintaining the confidentiality of your login information and for activities conducted through your account.</p>
      <p>Please notify us if you believe your account has been accessed without authorization.</p>
      <p>We reserve the right to suspend or terminate accounts involved in misuse, fraudulent activity or violations of these Terms.</p>

      <h4 class="about-subtitle">3. Product Information</h4>
      <p>We make reasonable efforts to display accurate product descriptions, images, colours, measurements and availability.</p>
      <p>However, slight variations in colour, texture, print, stitching or appearance may occur due to photography, lighting, screen settings and manufacturing processes.</p>
      <p>Product availability is subject to change without prior notice.</p>

      <h4 class="about-subtitle">4. Pricing &amp; Payments</h4>
      <p>All prices displayed on our website are in Indian Rupees (INR).</p>
      <p>We may offer payment methods including UPI, credit/debit cards, net banking, wallets and other payment options made available through our payment partners.</p>
      <p>We reserve the right to change prices, product details or offers at any time.</p>
      <p>If a pricing or listing error occurs, we reserve the right to cancel the affected order and will communicate with the customer where appropriate.</p>

      <h4 class="about-subtitle">5. Orders</h4>
      <p>Placing an order constitutes a request to purchase the selected products.</p>
      <p>We reserve the right to accept, reject or cancel an order in certain circumstances, including product unavailability, pricing errors, suspected fraudulent activity or technical issues.</p>
      <p>If an order is cancelled after payment has been received, the applicable amount will be refunded through the appropriate payment method, subject to the circumstances of the cancellation.</p>

      <h4 class="about-subtitle">6. Shipping &amp; Delivery</h4>
      <p>Orders are generally processed and dispatched within 1–2 business days, unless otherwise stated on the product or during checkout.</p>
      <p>Delivery timelines may vary depending on the destination, courier partner, weather, holidays and other circumstances beyond our reasonable control.</p>
      <p>Once an order has been dispatched, tracking information may be shared through email, SMS or WhatsApp.</p>

      <h4 class="about-subtitle">7. Returns &amp; Exchanges</h4>
      <p>Eligible products may be returned or exchanged within 7 days of delivery, subject to our Return &amp; Exchange Policy.</p>
      <p>Products must be unused, unwashed, undamaged and returned with their original packaging, tags and accessories.</p>
      <p>Products that have been worn, washed, damaged or altered may not be eligible for return or exchange.</p>
      <p>Customized products and products specifically identified as final sale may not be eligible for return or exchange.</p>
      <p>Additional conditions may apply under our Return &amp; Exchange Policy.</p>

      <h4 class="about-subtitle">8. Intellectual Property</h4>
      <p>All content available on the Likshora website, including brand names, logos, designs, photographs, graphics, text, product descriptions, videos and other materials, belongs to or is licensed to Likshora unless otherwise stated.</p>
      <p>You may not copy, reproduce, modify, distribute, publish or commercially use our content without prior written permission.</p>

      <h4 class="about-subtitle">9. Website Use</h4>
      <p>You agree not to misuse our website or attempt to:<br>
      • Access unauthorized areas of the website<br>
      • Interfere with website functionality<br>
      • Introduce malicious software<br>
      • Use the website for fraudulent purposes<br>
      • Copy or misuse our content<br>
      • Conduct activities that may harm Likshora or its customers</p>

      <h4 class="about-subtitle">10. Third-Party Services</h4>
      <p>Our website may use third-party services such as payment gateways, logistics providers, analytics services and other technology providers.</p>
      <p>Their services may be subject to their own terms and privacy policies.</p>
      <p>Likshora is not responsible for interruptions or failures caused solely by third-party services.</p>

      <h4 class="about-subtitle">11. Limitation of Liability</h4>
      <p>To the extent permitted by applicable law, Likshora will not be responsible for indirect or consequential losses arising from the use of our website or products.</p>
      <p>We are also not responsible for delays or failures caused by circumstances outside our reasonable control, including courier delays, natural events, technical failures or third-party service interruptions.</p>
      <p>Nothing in these Terms is intended to exclude any liability that cannot legally be excluded under applicable law.</p>

      <h4 class="about-subtitle">12. Changes to These Terms</h4>
      <p>We may update these Terms of Service from time to time.</p>
      <p>Changes will be published on this page. Your continued use of the website after changes are published constitutes acceptance of the updated Terms, to the extent permitted by applicable law.</p>

      <h4 class="about-subtitle">13. Governing Law</h4>
      <p>These Terms shall be governed by the applicable laws of India.</p>
      <p>Any disputes arising in connection with these Terms or your use of the website shall be subject to the applicable courts having jurisdiction.</p>

      <h4 class="about-subtitle">14. Contact Us</h4>
      <p>If you have any questions, concerns or complaints regarding these Terms:</p>
      <p class="about-quote">Email: <a href="mailto:support@likshora.com" style="color:inherit; text-decoration:underline;">support@likshora.com</a><br>
      Support Hours: Monday to Saturday, 10:00 AM – 6:00 PM (IST)<br>
      Address: Flat No. 401/402, Building No. 7B, Sector 2, Roop Rajat, Maan, Boisar East, Maharashtra, India.</p>

      <div class="about-footer-brand">
        <strong>LIKSHORA</strong>
        <span>Where Tradition Meets Tomorrow.</span>
      </div>
    </div>
  </div>`;
        document.body.appendChild(overlay);
      }
      return overlay;
    }

    document.addEventListener("click", function(e) {
      const isNavAbout = e.target.closest("#navAboutBtn, #navAboutBtnFooter");
      const isStoryLink = e.target.closest("#navStoryBtn, #navStoryBtnFooter") || (e.target.tagName === "A" && e.target.textContent.trim() === "Our Story");
      const isSustainLink = e.target.closest("#navSustainabilityBtnFooter") || (e.target.tagName === "A" && e.target.textContent.trim() === "Sustainability");
      const isCareersLink = e.target.closest("#navCareersBtnFooter") || (e.target.tagName === "A" && e.target.textContent.trim() === "Careers");
      const isPrivacyLink = e.target.closest("#navPrivacyBtnFooter") || (e.target.tagName === "A" && (e.target.textContent.trim().toLowerCase() === "privacy policy" || e.target.textContent.trim().toLowerCase() === "privacy"));
      const isTermsLink = e.target.closest("#navTermsBtnFooter") || (e.target.tagName === "A" && (e.target.textContent.trim().toLowerCase() === "terms of service" || e.target.textContent.trim().toLowerCase() === "terms"));
      const isAboutCloseBtn = e.target.closest("#aboutClose");
      const isStoryCloseBtn = e.target.closest("#storyClose");
      const isSustainCloseBtn = e.target.closest("#sustainabilityClose");
      const isCareersCloseBtn = e.target.closest("#careersClose");
      const isPrivacyCloseBtn = e.target.closest("#privacyClose");
      const isTermsCloseBtn = e.target.closest("#termsClose");

      if (isNavAbout) {
        e.preventDefault();
        e.stopPropagation();
        ensureAboutModal();
        if (window.Modal) window.Modal.open("aboutOverlay");
      } else if (isStoryLink) {
        e.preventDefault();
        e.stopPropagation();
        ensureStoryModal();
        if (window.Modal) window.Modal.open("storyOverlay");
      } else if (isSustainLink) {
        e.preventDefault();
        e.stopPropagation();
        ensureSustainabilityModal();
        if (window.Modal) window.Modal.open("sustainabilityOverlay");
      } else if (isCareersLink) {
        e.preventDefault();
        e.stopPropagation();
        ensureCareersModal();
        if (window.Modal) window.Modal.open("careersOverlay");
      } else if (isPrivacyLink) {
        e.preventDefault();
        e.stopPropagation();
        ensurePrivacyModal();
        if (window.Modal) window.Modal.open("privacyOverlay");
      } else if (isTermsLink) {
        e.preventDefault();
        e.stopPropagation();
        ensureTermsModal();
        if (window.Modal) window.Modal.open("termsOverlay");
      } else if (isAboutCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("aboutOverlay");
      } else if (isStoryCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("storyOverlay");
      } else if (isSustainCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("sustainabilityOverlay");
      } else if (isCareersCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("careersOverlay");
      } else if (isPrivacyCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("privacyOverlay");
      } else if (isTermsCloseBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (window.Modal) window.Modal.close("termsOverlay");
      }
    });
  }

  function openSearch() {
    const searchPanel = document.getElementById("searchPanel");
    const searchInput = document.getElementById("searchInput");
    if (searchPanel) searchPanel.classList.add("open");
    if (searchInput) searchInput.focus();
  }

  function closeSearch() {
    const searchPanel = document.getElementById("searchPanel");
    const searchResults = document.getElementById("searchResults");
    const searchInput = document.getElementById("searchInput");
    if (searchPanel) searchPanel.classList.remove("open");
    if (searchResults) {
      searchResults.classList.remove("open");
      searchResults.innerHTML = "";
    }
    if (searchInput) searchInput.value = "";
  }

  function updateCartBadge(count) {
    const cartCountEl = document.getElementById("cartCount");
    if (cartCountEl) {
      cartCountEl.textContent = count || 0;
    }
  }

  function updateUserAvatar(user) {
    const svgIcon = document.querySelector(".account-icon");
    const avatarEl = document.getElementById("userAvatar");
    if (!svgIcon || !avatarEl) return;

    if (user) {
      avatarEl.textContent = window.Formatters ? window.Formatters.getInitials(user.name) : "?";
      avatarEl.classList.remove("hidden");
      svgIcon.style.display = "none";
    } else {
      avatarEl.classList.add("hidden");
      svgIcon.style.display = "";
    }
  }

  function getProfileRedirectPath(page) {
    const path = window.location.pathname;
    if (path.includes("/pages/profile/")) {
      return page;
    } else if (path.includes("/pages/customer/") || path.includes("/pages/auth/")) {
      return "../profile/" + page;
    } else {
      return "pages/profile/" + page;
    }
  }

  function getLoginRedirectPath() {
    const path = window.location.pathname;
    if (path.includes("/pages/auth/")) {
      return "login.html";
    } else if (path.includes("/pages/customer/") || path.includes("/pages/profile/")) {
      return "../auth/login.html";
    } else {
      return "pages/auth/login.html";
    }
  }

  function getWishlistRedirectPath() {
    const path = window.location.pathname;
    if (path.includes("/pages/profile/")) {
      return "wishlist.html";
    } else if (path.includes("/pages/customer/") || path.includes("/pages/auth/")) {
      return "../profile/wishlist.html";
    } else {
      return "pages/profile/wishlist.html";
    }
  }

  function initAccountToggle() {
    const accountToggle = document.getElementById("accountToggle");
    if (!accountToggle) return;

    accountToggle.addEventListener("click", function(e) {
      const user = window.StorageUtils ? (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)) : null;
      e.preventDefault();
      e.stopPropagation();
      if (user) {
        window.location.href = getProfileRedirectPath("profile.html");
      } else {
        window.location.href = getLoginRedirectPath();
      }
    });
  }

  function getCartRedirectPath() {
    const path = window.location.pathname;
    if (path.includes("/pages/customer/")) {
      return "cart.html";
    } else if (path.includes("/pages/profile/")) {
      return "cart.html";
    } else if (path.includes("/pages/auth/")) {
      return "../customer/cart.html";
    } else {
      return "pages/customer/cart.html";
    }
  }

  function getCheckoutRedirectPath() {
    const path = window.location.pathname;
    if (path.includes("/pages/customer/")) {
      return "checkout.html";
    } else if (path.includes("/pages/profile/") || path.includes("/pages/auth/")) {
      return "../customer/checkout.html";
    } else {
      return "pages/customer/checkout.html";
    }
  }

  function isLoggedIn() {
    return Boolean(window.StorageUtils && (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)));
  }

  function initHeaderActions() {
    const wishToggle = document.getElementById("wishToggle");
    if (wishToggle) {
      wishToggle.addEventListener("click", function(e) {
        const user = window.StorageUtils ? (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)) : null;
        e.preventDefault();
        e.stopPropagation();
        if (user) {
          window.location.href = getWishlistRedirectPath();
        } else {
          window.location.href = getLoginRedirectPath();
        }
      });
    }

    const cartToggle = document.getElementById("cartToggle");
    if (cartToggle) {
      cartToggle.addEventListener("click", function(e) {
        if (typeof window.renderCart === "function") {
          window.renderCart();
        }
        const cartDrawer = document.getElementById("cartDrawer");
        if (cartDrawer) {
          if (window.Modal) window.Modal.open("cartDrawer");
          const drawerOverlay = document.getElementById("drawerOverlay");
          if (drawerOverlay) drawerOverlay.classList.add("open");
        } else {
          window.location.href = getCartRedirectPath();
        }
      });
    }

    const checkoutBtn = document.getElementById("checkoutBtn");
    if (checkoutBtn) {
      checkoutBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];
        if (cart.length === 0) {
          if (window.Toast) window.Toast.show("Your bag is empty");
          return;
        }
        window.location.href = getCheckoutRedirectPath();
      });
    }
  }

  function initNavLinks() {
    const mainNav = document.getElementById("mainNav");
    const menuToggle = document.getElementById("menuToggle");
    if (mainNav) {
      mainNav.querySelectorAll("a, button").forEach(function(link) {
        link.addEventListener("click", function() {
          if (mainNav.classList.contains("open")) {
            mainNav.classList.remove("open");
            if (menuToggle) menuToggle.classList.remove("open");
          }
        });
      });
    }
  }

  function syncCartBadge() {
    if (typeof window.renderCart === "function") {
      window.renderCart();
    } else {
      const cart = window.StorageUtils ? window.StorageUtils.readJSON("rv_cart", []) : [];
      const count = cart.reduce(function(sum, item) { return sum + (item.qty || 1); }, 0);
      updateCartBadge(count);
    }
  }

  function syncUserSession() {
    const user = window.StorageUtils ? (window.StorageUtils.readJSON("rv_current_user", null) || window.StorageUtils.readJSON("rv_user", null)) : null;
    updateUserAvatar(user);
    syncCartBadge();
  }

  return {
    init: function() {
      initHeaderControls();
      initAccountToggle();
      initHeaderActions();
      initNavLinks();
      syncUserSession();
      window.addEventListener("storage", function(e) {
        if (e.key === "rv_cart") {
          syncCartBadge();
        }
      });
    },
    openSearch: openSearch,
    closeSearch: closeSearch,
    updateCartBadge: updateCartBadge,
    syncCartBadge: syncCartBadge,
    updateUserAvatar: updateUserAvatar,
    getProfileRedirectPath: getProfileRedirectPath,
    getLoginRedirectPath: getLoginRedirectPath,
    getWishlistRedirectPath: getWishlistRedirectPath,
    getCartRedirectPath: getCartRedirectPath,
    getCheckoutRedirectPath: getCheckoutRedirectPath,
    isLoggedIn: isLoggedIn
  };
})();

// Global Unified Cart Renderer for all pages and components
window.renderCart = function() {
  const CART_KEY = "rv_cart";
  const cart = window.StorageUtils ? window.StorageUtils.readJSON(CART_KEY, []) : [];

  // 1. Update Drawer Items if present
  const itemsWrap = document.getElementById("drawerItems");
  const totalEl = document.getElementById("drawerTotal");

  if (itemsWrap && totalEl) {
    if (cart.length === 0) {
      itemsWrap.innerHTML = '<p class="drawer-empty" id="drawerEmpty">Your bag is empty — the edit is waiting.</p>';
    } else {
      itemsWrap.innerHTML = cart.map(function(item) {
        let rawImg = item.image || (item.images && item.images.length > 0 ? (typeof item.images[0] === 'string' ? item.images[0] : item.images[0].url) : "");
        let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;
        let itemTotal = item.price * (item.qty || 1);

        return `
          <div class="drawer-item" data-id="${item.id}" data-size="${item.size || 'M'}">
            <div class="media-slot" data-placeholder="Product">${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(item.name) + '">' : ''}</div>
            <div class="drawer-item-info" style="display:flex; flex-direction:column; gap:.2em;">
              <p class="drawer-item-name" style="font-family:var(--font-display); font-size:.92rem; margin:0;">${window.Formatters.escapeHTML(item.name)}</p>
              ${item.size ? `<p class="drawer-item-size" style="font-size:.78rem; color:var(--ink-soft); margin:0;">Size: <strong>${item.size}</strong></p>` : ''}
              ${item.color ? `<p class="drawer-item-color" style="font-size:.78rem; color:var(--ink-soft); margin:0;">Color: <strong>${item.color}</strong></p>` : ''}
              <p class="drawer-item-price" style="font-size:.8rem; color:var(--ink-soft); margin:0;">Price: ${window.Formatters.formatINR(item.price)}</p>
              <div class="drawer-item-qty" style="display:flex; align-items:center; gap:.4em; margin-top:.3em;">
                <button type="button" class="qty-btn" data-qty-down="${item.id}" data-size="${item.size || 'M'}">-</button>
                <span style="font-size:.82rem; font-weight:500;">Qty: ${item.qty || 1}</span>
                <button type="button" class="qty-btn" data-qty-up="${item.id}" data-size="${item.size || 'M'}">+</button>
              </div>
              <p class="drawer-item-total" style="font-size:.82rem; font-weight:600; color:var(--ink); margin-top:.2em;">Total: ${window.Formatters.formatINR(itemTotal)}</p>
            </div>
            <button class="drawer-item-remove" data-remove="${item.id}" data-size="${item.size || 'M'}">Remove</button>
          </div>
        `;
      }).join("");
    }
    const total = cart.reduce(function(sum, item) { return sum + item.price * (item.qty || 1); }, 0);
    totalEl.textContent = window.Formatters ? window.Formatters.formatINR(total) : '₹' + total;
  }

  // 2. Update Dedicated Cart Page Table if present
  const tableBody = document.getElementById("cartTableBody");
  const layoutEl = document.getElementById("cartPageLayout");
  const emptyNoticeEl = document.getElementById("cartEmptyNotice");
  const subtotalEl = document.getElementById("cartSubtotal");
  const cartTotalValEl = document.getElementById("cartTotalVal");

  if (tableBody && layoutEl && emptyNoticeEl) {
    if (cart.length === 0) {
      layoutEl.style.display = "none";
      emptyNoticeEl.classList.remove("hidden");
    } else {
      layoutEl.style.display = "";
      emptyNoticeEl.classList.add("hidden");
      tableBody.innerHTML = cart.map(function(item) {
        let rawImg = item.image || (item.images && item.images.length > 0 ? (typeof item.images[0] === 'string' ? item.images[0] : item.images[0].url) : "");
        let imgPath = window.Formatters && window.Formatters.formatProductImage ? window.Formatters.formatProductImage(rawImg, true) : rawImg;
        let itemTotal = item.price * (item.qty || 1);

        return `
          <tr data-id="${item.id}" data-size="${item.size || 'M'}">
            <td>
              <div class="cart-item-info">
                <div class="cart-item-thumb">
                  ${imgPath ? '<img src="' + imgPath + '" alt="' + window.Formatters.escapeHTML(item.name) + '">' : ''}
                </div>
                <div>
                  <h4 class="cart-item-name">${window.Formatters.escapeHTML(item.name)}</h4>
                  <p class="cart-item-variant">Size: <strong>${item.size || 'M'}</strong>${item.color ? ' | Color: <strong>' + item.color + '</strong>' : ''}</p>
                </div>
              </div>
            </td>
            <td>${window.Formatters.formatINR(item.price)}</td>
            <td>
              <div class="cart-qty-ctrl" style="display:flex; align-items:center; gap:.4em;">
                <button type="button" class="qty-btn" data-action="down" style="width:24px; height:24px; border:1px solid var(--stone); background:none; border-radius:50%; cursor:pointer; display:inline-flex; align-items:center; justify-content:center;">-</button>
                <span style="font-size:.88rem; font-weight:500; min-width:18px; text-align:center;">${item.qty || 1}</span>
                <button type="button" class="qty-btn" data-action="up" style="width:24px; height:24px; border:1px solid var(--stone); background:none; border-radius:50%; cursor:pointer; display:inline-flex; align-items:center; justify-content:center;">+</button>
              </div>
            </td>
            <td style="font-weight: 600;">${window.Formatters.formatINR(itemTotal)}</td>
            <td style="text-align: right;">
              <button type="button" class="cart-remove-btn" data-action="remove">Remove</button>
            </td>
          </tr>
        `;
      }).join("");
    }
    const total = cart.reduce(function(sum, item) { return sum + item.price * (item.qty || 1); }, 0);
    if (subtotalEl) subtotalEl.textContent = window.Formatters ? window.Formatters.formatINR(total) : '₹' + total;
    if (cartTotalValEl) cartTotalValEl.textContent = window.Formatters ? window.Formatters.formatINR(total) : '₹' + total;
  }

  // 3. Update Navbar Badge
  const count = cart.reduce(function(sum, item) { return sum + (item.qty || 1); }, 0);
  const cartCountEl = document.getElementById("cartCount");
  if (cartCountEl) cartCountEl.textContent = count || 0;
};
