/**
 * tanhdev.com - Portfolio Shell Controller (Vanilla JS < 3KB)
 * Zero Framework Bloat | High Performance | WCAG Accessible
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    // ── 1. Continuous Smooth-Scroll Rail Spy ────────────────────────────────
    const sections = document.querySelectorAll('.portfolio-section[id]');
    const railLinks = document.querySelectorAll('.rail-nav-link[href^="#"], .mobile-dock-link[href^="#"]');

    if ('IntersectionObserver' in window && sections.length > 0) {
      const spyObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            railLinks.forEach((link) => {
              const active = link.getAttribute('href') === `#${id}`;
              link.classList.toggle('active', active);
              if (active) {
                link.setAttribute('aria-current', 'true');
              } else {
                link.removeAttribute('aria-current');
              }
            });
            if (history.replaceState && id) {
              history.replaceState(null, null, `#${id}`);
            }
          }
        });
      }, { rootMargin: '-20% 0px -55% 0px', threshold: 0.1 });

      sections.forEach((s) => spyObserver.observe(s));
    }

    // Smooth scroll on anchor clicks
    document.querySelectorAll('.rail-nav-link[href^="#"], .mobile-dock-link[href^="#"]').forEach((link) => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });

    // ── 2. SVG Circular & Linear Skill Meters Animation ────────────────────
    const skillsContainer = document.querySelector('.skills-meters-group');
    if (skillsContainer && 'IntersectionObserver' in window) {
      const skillsObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Animate circular SVGs (r = 34, C = 2 * PI * 34 ≈ 213.63)
            document.querySelectorAll('.skill-circle-meter').forEach((circle) => {
              const percent = parseFloat(circle.dataset.percent || 0);
              const circumference = 2 * Math.PI * 34;
              const offset = circumference - (circumference * percent) / 100;
              circle.style.strokeDashoffset = offset;
            });
            // Animate linear gauges
            document.querySelectorAll('.skill-linear-fill').forEach((bar) => {
              const percent = bar.dataset.percent || 0;
              bar.style.width = `${percent}%`;
            });
            obs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.2 });

      skillsObserver.observe(skillsContainer);
    }

    // ── 3. Bento Category Filter ───────────────────────────────────────────
    const filterBtns = document.querySelectorAll('.bento-filter-btn');
    const bentoCards = document.querySelectorAll('.bento-card[data-category]');

    filterBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        filterBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = (btn.dataset.filter || 'all').toLowerCase();

        bentoCards.forEach((card) => {
          const cats = (card.dataset.category || '').toLowerCase();
          const match = filter === 'all' || cats.includes(filter);
          card.classList.toggle('is-filtered-out', !match);
        });
      });
    });

    // ── 4. Mobile Profile Drawer & Backdrop ────────────────────────────────
    const drawerOpenBtns = document.querySelectorAll('#mobile-drawer-toggle, .mobile-drawer-trigger');
    const drawerCloseBtn = document.getElementById('drawer-close-btn');
    const backdrop = document.getElementById('drawer-backdrop');

    function openDrawer() {
      document.body.classList.add('drawer-open');
      if (backdrop) backdrop.classList.add('active');
    }
    function closeDrawer() {
      document.body.classList.remove('drawer-open');
      if (backdrop) backdrop.classList.remove('active');
    }

    drawerOpenBtns.forEach((btn) => btn.addEventListener('click', openDrawer));
    if (drawerCloseBtn) drawerCloseBtn.addEventListener('click', closeDrawer);
    if (backdrop) backdrop.addEventListener('click', closeDrawer);

    document.addEventListener('keydown', (e) => {
      if ((e.key === 'Escape' || e.key === 'Esc') && document.body.classList.contains('drawer-open')) {
        closeDrawer();
      }
    });

    // ── 5. Rail Action Hooks (Theme Toggle & Search Modal) ─────────────────
    const railThemeBtns = document.querySelectorAll('#rail-theme-toggle, .dock-theme-toggle');
    railThemeBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const nativeThemeBtn = document.getElementById('theme-toggle');
        if (nativeThemeBtn) {
          nativeThemeBtn.click();
        }
      });
    });

    const railSearchBtns = document.querySelectorAll('#rail-search-trigger, .dock-search-trigger');
    railSearchBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const nativeSearchBtn = document.getElementById('search-nav-btn') || document.querySelector('.search-trigger-btn');
        if (nativeSearchBtn) {
          nativeSearchBtn.click();
        }
      });
    });
  });
})();
