/**
 * 星羽创媒 CMS — 前端动态加载器
 * 从 API 获取数据，替换页面硬编码内容
 */
(function() {
  'use strict';

  const API_BASE = '';  // 同源，无需前缀

  // ── 工具函数 ──
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return (ctx || document).querySelectorAll(sel); }
  function setHTML(el, html) { if (el) el.innerHTML = html; }
  function setText(el, text) { if (el) el.textContent = text; }

  // ── 加载文案 ──
  async function loadContent() {
    try {
      const res = await fetch(`${API_BASE}/api/content?page=index`);
      if (!res.ok) return;
      const data = await res.json();

      // Hero 首屏
      if (data.hero) {
        const h = data.hero;
        const badge = $('[data-cms="hero-badge"]');
        const title = $('[data-cms="hero-title"]');
        const sub = $('[data-cms="hero-subtitle"]');
        if (badge) badge.textContent = h.badge || '';
        if (title) title.innerHTML = h.title || '';
        if (sub) sub.innerHTML = h.subtitle || '';

        // 统计数据
        for (let i = 1; i <= 4; i++) {
          const numEl = $(`[data-cms="hero-stat-${i}-num"]`);
          const lblEl = $(`[data-cms="hero-stat-${i}-label"]`);
          if (numEl) numEl.textContent = h[`stat_${i}_num`] || '';
          if (lblEl) lblEl.textContent = h[`stat_${i}_label`] || '';
        }
      }

      // 关于我们
      if (data.about) {
        const a = data.about;
        const title = $('[data-cms="about-title"]');
        if (title) title.textContent = a.title || '';
        for (let i = 1; i <= 4; i++) {
          const el = $(`[data-cms="about-desc-${i}"]`);
          if (el && a[`desc_${i}`]) el.innerHTML = a[`desc_${i}`];
        }
      }

      // AI 内容生产区块
      if (data['ai-production']) {
        const ap = data['ai-production'];
        const label = $('[data-cms="ap-label"]');
        const title = $('[data-cms="ap-title"]');
        const desc = $('[data-cms="ap-desc"]');
        if (label) label.textContent = ap.label || '';
        if (title) title.textContent = ap.title || '';
        if (desc) desc.textContent = ap.desc || '';

        for (let i = 1; i <= 4; i++) {
          const numEl = $(`[data-cms="ap-stat-${i}-num"]`);
          const lblEl = $(`[data-cms="ap-stat-${i}-label"]`);
          if (numEl) numEl.textContent = ap[`stat_${i}_num`] || '';
          if (lblEl) lblEl.textContent = ap[`stat_${i}_label`] || '';
        }
      }

      // 联系方式
      if (data.contact) {
        const c = data.contact;
        const phone = $('[data-cms="contact-phone"]');
        const email = $('[data-cms="contact-email"]');
        const address = $('[data-cms="contact-address"]');
        const wechat = $('[data-cms="contact-wechat"]');
        if (phone) phone.textContent = c.phone || '';
        if (email) email.textContent = c.email || '';
        if (address) address.textContent = c.address || '';
        if (wechat) wechat.textContent = c.wechat || '';
      }

      // 页脚
      if (data.footer) {
        const slogan = $('[data-cms="footer-slogan"]');
        if (slogan) slogan.innerHTML = data.footer.slogan || '';
      }

    } catch (e) {
      console.warn('[CMS] 文案加载失败，使用静态内容:', e);
    }
  }

  // ── 加载案例 ──
  async function loadCases() {
    try {
      const container = $('[data-cms="case-grid"]');
      if (!container) return;

      // 判断当前页面：首页只加载精选案例，子页面加载全部
      const isHomePage = !window.location.pathname.includes('ai-production');
      const apiUrl = isHomePage
        ? `${API_BASE}/api/cases?category=ai-production&show_on_home=true&limit=50`
        : `${API_BASE}/api/cases?category=ai-production&limit=50`;

      const res = await fetch(apiUrl);
      if (!res.ok) return;
      const cases = await res.json();
      if (!cases.length) return;

      container.innerHTML = cases.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const tagsHTML = (c.tags || []).map(t => `<span>${t}</span>`).join('');
        const videoSrc = c.video_file ? c.video_file : '';
        const videoPath = videoSrc ? `/uploads/videos/${encodeURIComponent(videoSrc)}` : '';
        const thumbnailPath = c.thumbnail ? `/uploads/images/${c.thumbnail}` : '';

        // 背景：优先使用缩略图，否则用品牌色渐变
        const bgColors = [
          'linear-gradient(135deg, #1a1040 0%, #0d0d2b 40%, #1a1040 100%)',
          'linear-gradient(135deg, #0f1a2e 0%, #0a0f1f 40%, #0f1a2e 100%)',
          'linear-gradient(135deg, #111122 0%, #0b0b1a 40%, #111122 100%)',
          'linear-gradient(135deg, #1a1a2e 0%, #0f0f1f 40%, #1a1a2e 100%)'
        ];
        const bgStyle = thumbnailPath
          ? `background: url(${thumbnailPath}) center/cover no-repeat;`
          : `background: ${bgColors[i % 4]};`;

        const mp4Path = thumbnailPath ? thumbnailPath.replace('.gif', '.mp4') : '';

        return `
          <div class="cat-card cat-inline-video-card reveal${delay}" data-video="${videoPath}">
            ${thumbnailPath ? `<video class="cat-bg-video" src="${mp4Path}" muted autoplay loop playsinline disableRemotePlayback></video><img class="cat-bg-fallback" src="${thumbnailPath}" alt="">` : `<div class="cat-bg-video" style="${bgStyle}"></div>`}
            <div class="cat-overlay"></div>
            <div class="cat-video-content">
              <h3>${c.title}</h3>
              ${c.en_name ? `<div class="cat-en">${c.en_name}</div>` : ''}
              <p class="cat-desc">${c.description || ''}</p>
            </div>
            <video class="cat-inline-video" preload="none" playsinline controls></video>
            <button class="cat-video-close" aria-label="关闭视频">✕</button>
          </div>`;
      }).join('');

      // MutationObserver 会自动重新绑定卡片交互

      // 重新触发 reveal 动画
      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        container.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] 案例加载失败，使用静态内容:', e);
    }
  }

  // ── 加载团队 ──
  async function loadTeam() {
    try {
      const grid = $('[data-cms="team-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/team`);
      if (!res.ok) return;
      const members = await res.json();
      if (!members.length) return;

      // 跳过创始人（在 founder-card 中单独处理）
      const coreMembers = members.filter(m => !m.is_founder);

      grid.innerHTML = coreMembers.map((m, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        return `
          <div class="team-card reveal${delay}">
            <h3>${m.name}</h3>
            <p class="role">${m.role}</p>
            <p class="bio">${m.bio}</p>
          </div>`;
      }).join('');

      // 重新触发 reveal 动画
      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

      // 更新创始人信息
      const founder = members.find(m => m.is_founder);
      if (founder) {
        const fname = $('[data-cms="founder-name"]');
        const frole = $('[data-cms="founder-role"]');
        const fbio = $('[data-cms="founder-bio"]');
        if (fname) fname.textContent = founder.name;
        if (frole) frole.textContent = founder.role;
        if (fbio) fbio.textContent = founder.bio;

        if (founder.photo) {
          const fphoto = $('[data-cms="founder-photo"] img');
          if (fphoto) {
            fphoto.src = `/uploads/images/${founder.photo}`;
          }
        }
      }

    } catch (e) {
      console.warn('[CMS] 团队加载失败，使用静态内容:', e);
    }
  }

  // ── 视频播放绑定 ──
  function bindVideoPlay() {
    document.querySelectorAll('.case-play').forEach(btn => {
      btn.onclick = function() {
        const video = this.previousElementSibling;
        if (!video) return;
        const source = video.querySelector('source[data-src]');
        // 修复：用 currentSrc 判断是否已加载，而非 video.src
        if (source && !video.currentSrc) {
          video.src = source.dataset.src;
          source.removeAttribute('data-src');
        }
        if (video.paused) { video.play(); this.style.display = 'none'; }
        else { video.pause(); this.textContent = '▶'; this.style.display = 'flex'; }
      };
    });
    document.querySelectorAll('video').forEach(v => {
      v.onclick = function() {
        if (!this.paused) { this.pause(); const b = this.nextElementSibling; if (b) { b.textContent = '▶'; b.style.display = 'flex'; } }
      };
      v.onended = function() { const b = this.nextElementSibling; if (b) { b.textContent = '▶'; b.style.display = 'flex'; } };
    });
  }

  // ── 加载培训卡片 ──
  async function loadTrainingCards() {
    try {
      const grid = $('[data-cms="training-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/training-cards`);
      if (!res.ok) return;
      const cards = await res.json();
      if (!cards.length) return;

      grid.innerHTML = cards.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const tagsHTML = c.tags.map(t => `<span>${t}</span>`).join('');
        const imagePath = c.image ? `images/${c.image}` : '';

        return `
          <div class="training-card reveal${delay}">
            <div class="tc-visual">${imagePath ? `<img src="${imagePath}" alt="${c.title}">` : ''}</div>
            <div class="tc-body">
              <h3>${c.title}</h3>
              <p>${c.description}</p>
              <div class="tc-tags">${tagsHTML}</div>
            </div>
          </div>`;
      }).join('');

      // 重新触发 reveal 动画
      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] 培训卡片加载失败，使用静态内容:', e);
    }
  }

  // ── 加载文旅IP卡片 ──
  async function loadEventCards() {
    try {
      const grid = $('[data-cms="event-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/event-cards`);
      if (!res.ok) return;
      const cards = await res.json();
      if (!cards.length) return;

      const badgeColors = {
        'emerald': 'border-color:var(--emerald);color:var(--emerald);background:rgba(16,185,129,0.08)',
        'amber': 'border-color:var(--amber);color:var(--amber);background:rgba(245,158,11,0.08)',
        'violet': 'border-color:var(--violet);color:var(--violet);background:rgba(139,92,246,0.08)',
        'blue': 'border-color:var(--blue);color:var(--blue);background:rgba(59,130,246,0.08)',
      };

      grid.innerHTML = cards.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const imagePath = c.image ? `images/${c.image}` : '';
        const badgeStyle = badgeColors[c.badge_color] || badgeColors['emerald'];
        const tagsHTML = c.tags && c.tags.length ? `<div class="tc-tags">${c.tags.map(t => `<span>${t}</span>`).join('')}</div>` : '';

        return `
          <div class="visual-card reveal${delay}">
            <div class="vc-visual">${imagePath ? `<img src="${imagePath}" alt="${c.title}">` : ''}</div>
            <div class="vc-body">
              <h3>${c.title}</h3>
              <p>${c.description}</p>
              ${tagsHTML}
              ${c.badge ? `<span class="badge-soon" style="${badgeStyle}">${c.badge}</span>` : ''}
            </div>
          </div>`;
      }).join('');

      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] 文旅IP卡片加载失败，使用静态内容:', e);
    }
  }

  // ── 加载企业AI Agent卡片 ──
  async function loadAgentCards() {
    try {
      const grid = $('[data-cms="agent-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/agent-cards`);
      if (!res.ok) return;
      const cards = await res.json();
      if (!cards.length) return;

      grid.innerHTML = cards.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const imagePath = c.image ? `images/${c.image}` : '';
        const tagsHTML = c.tags && c.tags.length ? `<div class="tc-tags">${c.tags.map(t => `<span>${t}</span>`).join('')}</div>` : '';

        return `
          <div class="visual-card reveal${delay}">
            <div class="vc-visual">${imagePath ? `<img src="${imagePath}" alt="${c.title}">` : ''}</div>
            <div class="vc-body">
              <h3>${c.title}</h3>
              <p>${c.description}</p>
              ${tagsHTML}
            </div>
          </div>`;
      }).join('');

      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] 企业AI Agent卡片加载失败，使用静态内容:', e);
    }
  }

  // ── 加载AI Studio功能卡片 ──
  async function loadStudioCards() {
    try {
      const grid = $('[data-cms="studio-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/studio-cards`);
      if (!res.ok) return;
      const cards = await res.json();
      if (!cards.length) return;

      grid.innerHTML = cards.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const imagePath = c.image ? `images/${c.image}` : '';
        const tagsHTML = c.tags && c.tags.length ? `<div class="tc-tags">${c.tags.map(t => `<span>${t}</span>`).join('')}</div>` : '';

        return `
          <div class="visual-card reveal${delay}">
            <div class="vc-visual">${imagePath ? `<img src="${imagePath}" alt="${c.title}">` : ''}</div>
            <div class="vc-body">
              <h3>${c.title}</h3>
              <p>${c.description}</p>
              ${tagsHTML}
            </div>
          </div>`;
      }).join('');

      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] AI Studio功能卡片加载失败，使用静态内容:', e);
    }
  }

  // ── 加载AI Studio平台卡片 ──
  async function loadPlatformCards() {
    try {
      const grid = $('[data-cms="platform-grid"]');
      if (!grid) return;

      const res = await fetch(`${API_BASE}/api/platform-cards`);
      if (!res.ok) return;
      const cards = await res.json();
      if (!cards.length) return;

      grid.innerHTML = cards.map((c, i) => {
        const delay = i > 0 ? ` reveal-d${Math.min(i, 5)}` : '';
        const imagePath = c.image ? `images/${c.image}` : '';
        const tagsHTML = c.tags && c.tags.length ? `<div class="tc-tags">${c.tags.map(t => `<span>${t}</span>`).join('')}</div>` : '';

        return `
          <div class="visual-card reveal${delay}">
            <div class="vc-visual">${imagePath ? `<img src="${imagePath}" alt="${c.title}">` : ''}</div>
            <div class="vc-body" style="text-align:center;">
              <h3 style="font-size:0.95rem;">${c.title}</h3>
              <p style="font-size:0.75rem;margin-bottom:0;">${c.description}</p>
              ${tagsHTML}
            </div>
          </div>`;
      }).join('');

      requestAnimationFrame(() => {
        const obs = new IntersectionObserver(entries => {
          entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); } });
        }, { threshold: 0.1 });
        grid.querySelectorAll('.reveal').forEach(el => obs.observe(el));
      });

    } catch (e) {
      console.warn('[CMS] AI Studio平台卡片加载失败，使用静态内容:', e);
    }
  }

  // ── 初始化 ──
  document.addEventListener('DOMContentLoaded', () => {
    // 检查页面是否有 data-cms 属性，有则加载动态内容
    if (document.querySelector('[data-cms]')) {
      loadContent();
      loadCases();
      loadTeam();
      loadTrainingCards();
      loadEventCards();
      loadAgentCards();
      loadStudioCards();
      loadPlatformCards();
    }
  });

})();
