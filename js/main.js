/**
 * 星羽创媒 - 官方网站交互脚本
 */

// 修复浏览器缓存导致刷新后内容消失
window.addEventListener('pageshow', function(e) {
    if (e.persisted) {
        document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
        document.querySelectorAll('.reveal-hidden').forEach(el => el.classList.add('revealed'));
    }
});

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initHeroParticles();
    initHeroAnimation();
    initScrollAnimations();
    initCaseFilter();
    initCounterAnimation();
    initSmoothScroll();
    initProcessSteps();
    initCaseVideos();
    initBackToTop();
    initContactForm();
});

/* ========== 导航栏 ========== */
function initNavigation() {
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    // 滚动时导航样式切换
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 移动端菜单切换
    navToggle.addEventListener('click', () => {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.classList.toggle('menu-open');
    });

    // 点击链接关闭菜单
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    });

    // 当前section高亮导航 - 修复最后section始终高亮的问题
    const sections = document.querySelectorAll('section[id]');
    window.addEventListener('scroll', () => {
        let current = '';
        const scrollY = window.scrollY + 150; // 偏移量用于更精准匹配
        sections.forEach(section => {
            const top = section.offsetTop;
            if (scrollY >= top) {
                current = section.getAttribute('id');
            }
        });
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

/* ========== Hero粒子背景 (Canvas绑制) ========== */
function initHeroParticles() {
    const container = document.getElementById('heroParticles');
    if (!container) return;

    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.inset = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const colors = ['#22D3EE', '#0B85DF', '#67E8F9', '#6366F1', '#ffffff'];
    const particles = [];
    const particleCount = 60;
    let mouseX = -1000;
    let mouseY = -1000;

    function resize() {
        canvas.width = container.offsetWidth;
        canvas.height = container.offsetHeight;
    }

    class Particle {
        constructor() {
            this.reset();
            this.y = Math.random() * canvas.height;
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = -10;
            this.size = Math.random() * 3 + 1.5;
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.speed = Math.random() * 0.5 + 0.3;
            this.opacity = Math.random() * 0.5 + 0.15;
            this.wobble = Math.random() * Math.PI * 2;
            this.wobbleSpeed = (Math.random() - 0.5) * 0.02;
            this.wobbleAmp = Math.random() * 0.5;
        }
        update() {
            this.y -= this.speed;
            this.wobble += this.wobbleSpeed;
            this.x += Math.sin(this.wobble) * this.wobbleAmp;

            // 鼠标交互 - 轻微吸引
            const dx = mouseX - this.x;
            const dy = mouseY - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 150 && dist > 0) {
                this.x += (dx / dist) * 0.3;
                this.y += (dy / dist) * 0.3;
            }

            if (this.y < -10) {
                this.reset();
                this.y = canvas.height + 10;
            }
            if (this.x < -10) this.x = canvas.width + 10;
            if (this.x > canvas.width + 10) this.x = -10;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity;
            ctx.fill();

            // 光晕效果
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * 2.5, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity * 0.1;
            ctx.fill();
        }
    }

    // 初始化粒子
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }

    // 鼠标跟踪
    container.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouseX = e.clientX - rect.left;
        mouseY = e.clientY - rect.top;
    });
    container.addEventListener('mouseleave', () => {
        mouseX = -1000;
        mouseY = -1000;
    });

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 绘制连线
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(34,211,238,0.06)';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        ctx.globalAlpha = 1;
        requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', resize);
    animate();
}

/* ========== Hero初始动画 ========== */
function initHeroAnimation() {
    const heroElements = document.querySelectorAll('.fade-up');
    heroElements.forEach(el => {
        requestAnimationFrame(() => {
            el.classList.add('visible');
        });
    });
}

/* ========== 滚动入场动画 ========== */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -60px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                const children = entry.target.querySelectorAll('.reveal-child');
                children.forEach((child, index) => {
                    child.style.transitionDelay = `${index * 0.1}s`;
                    child.classList.add('revealed');
                });
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.section-header, .capability-card, .case-card, .team-card, .geo-card, .training-card, .process-step, .stat-item').forEach(el => {
        el.classList.add('reveal-hidden');
        observer.observe(el);
    });
}

/* ========== 案例筛选 - 修复多分类支持 ========== */
function initCaseFilter() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const caseCards = document.querySelectorAll('.case-card');

    if (!filterBtns.length) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.dataset.filter;

            caseCards.forEach(card => {
                card.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                // 修复：支持多分类标签（空格分隔），使用 split + includes
                const categories = card.dataset.category.split(' ');
                const isMatch = filter === 'all' || categories.includes(filter);

                if (isMatch) {
                    card.style.opacity = '1';
                    card.style.transform = 'scale(1)';
                    card.style.maxHeight = '500px';
                    card.style.marginBottom = '24px';
                    card.style.pointerEvents = 'auto';
                    card.style.overflow = 'visible';
                } else {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    card.style.maxHeight = '0';
                    card.style.marginBottom = '0';
                    card.style.pointerEvents = 'none';
                    card.style.overflow = 'hidden';
                }
            });
        });
    });
}

/* ========== 数字滚动动画 ========== */
function initCounterAnimation() {
    const counters = document.querySelectorAll('.stat-number, .geo-num[data-target], .counter-animate[data-target]');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.dataset.target);
                const suffix = counter.dataset.suffix || '';
                const prefix = counter.dataset.prefix || '';
                const duration = 2000;
                const start = performance.now();
                const originalText = counter.textContent;

                function update(now) {
                    const elapsed = now - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                    const current = Math.floor(eased * target);
                    counter.textContent = prefix + current + suffix;
                    if (progress < 1) {
                        requestAnimationFrame(update);
                    }
                }

                requestAnimationFrame(update);
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.6 });

    counters.forEach(c => observer.observe(c));
}

/* ========== 平滑滚动 ========== */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = -30;
                const position = target.offsetTop - offset;
                window.scrollTo({
                    top: position,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/* ========== 流程步骤动画 ========== */
function initProcessSteps() {
    const steps = document.querySelectorAll('.process-step');
    const progressBar = document.querySelector('.process-progress-fill');

    if (!steps.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.5 });

    steps.forEach(step => observer.observe(step));

    const processSection = document.querySelector('.process-timeline');
    if (processSection && progressBar) {
        const progressObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                progressBar.style.width = '100%';
            }
        }, { threshold: 0.3 });
        progressObserver.observe(processSection);
    }
}

/* ========== 案例视频播放/暂停 ========== */
function toggleVideo(btn) {
    const video = btn.previousElementSibling;
    if (!video || video.tagName !== 'VIDEO') return;
    
    if (video.paused) {
        // 懒加载：首次播放时才设置 src
        const source = video.querySelector('source');
        if (source) {
            const src = source.getAttribute('data-src') || source.getAttribute('src');
            if (src && src !== source.src) {
                source.src = src;
                video.load();
            }
        }
        video.play().catch(e => console.log('Video play error:', e));
        btn.style.display = 'none';
    } else {
        video.pause();
        btn.style.display = 'flex';
        btn.textContent = '▶';
    }
}

function initCaseVideos() {
    document.querySelectorAll('.case-video').forEach(video => {
        video.addEventListener('click', function() {
            if (!this.paused) {
                this.pause();
                const btn = this.nextElementSibling;
                if (btn && btn.classList.contains('case-video-play')) {
                    btn.style.display = 'flex';
                    btn.textContent = '▶';
                }
            }
        });
    });
}

/* ========== 返回顶部按钮 ========== */
function initBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    let scrollTicking = false;
    window.addEventListener('scroll', () => {
        if (!scrollTicking) {
            requestAnimationFrame(() => {
                if (window.scrollY > 500) {
                    btn.classList.add('visible');
                } else {
                    btn.classList.remove('visible');
                }
                scrollTicking = false;
            });
            scrollTicking = true;
        }
    });

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/* ========== 联系表单处理 ========== */
function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    // 自定义 toast 容器
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.style.cssText = `
            position: fixed; top: 24px; right: 24px; z-index: 10000;
            display: flex; flex-direction: column; gap: 12px;
        `;
        document.body.appendChild(toastContainer);
    }

    function showToast(message, type) {
        const toast = document.createElement('div');
        const bgColor = type === 'success'
            ? 'linear-gradient(135deg, #10b981, #059669)'
            : 'linear-gradient(135deg, #ef4444, #dc2626)';
        const icon = type === 'success' ? '✓' : '✕';

        toast.style.cssText = `
            background: ${bgColor};
            color: #fff;
            padding: 14px 24px;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 500;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            display: flex; align-items: center; gap: 10px;
            animation: toastIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 380px;
        `;
        toast.innerHTML = `<span style="font-size:1.1rem;font-weight:700">${icon}</span> ${message}`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // 前端验证
        const name = form.querySelector('input[placeholder*="姓名"]');
        const phone = form.querySelector('input[type="tel"]');
        const service = form.querySelector('select');
        const message = form.querySelector('textarea');

        if (!name || !name.value.trim()) {
            showToast('请填写您的姓名', 'error');
            name.focus();
            return;
        }
        if (!phone || !phone.value.trim()) {
            showToast('请填写联系电话', 'error');
            phone.focus();
            return;
        }
        if (phone.value.trim() && !/^[\d\-+() ]{7,}$/.test(phone.value.trim())) {
            showToast('请填写有效的联系电话', 'error');
            phone.focus();
            return;
        }

        // 收集表单数据
        const formData = {
            name: name ? name.value.trim() : '',
            company: form.querySelector('input[placeholder*="公司"]')?.value.trim() || '',
            phone: phone ? phone.value.trim() : '',
            service: service ? service.value : '',
            message: message ? message.value.trim() : '',
            timestamp: new Date().toISOString()
        };

        // 模拟提交
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = '提交中...';
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.7';

        setTimeout(() => {
            showToast('咨询已提交，我们将尽快与您联系！', 'success');
            form.reset();
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            console.log('Form data:', formData);
        }, 1200);
    });

    // 实时输入反馈 - 输入框获得焦点时发光
    form.querySelectorAll('input, select, textarea').forEach(el => {
        el.addEventListener('focus', () => {
            el.closest('.form-group')?.classList.add('focused');
        });
        el.addEventListener('blur', () => {
            el.closest('.form-group')?.classList.remove('focused');
        });
    });
}

/* ========== 键盘导航 ========== */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const navMenu = document.querySelector('.nav-menu');
        const navToggle = document.getElementById('navToggle');
        if (navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    }
});