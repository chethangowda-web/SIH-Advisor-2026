'use strict';
/* SIH AURORA — ambient effects: boot splash, particles, cursor glow,
   3D tilt, parallax, header scroll state. All non-destructive & guarded. */

(function () {
  const finePointer = window.matchMedia('(pointer: fine)').matches;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (id) => document.getElementById(id);

  /* ── Boot splash ───────────────────────────────────────────── */
  const splash = $('bootSplash');
  function killSplash() {
    if (!splash) return;
    splash.classList.add('fade');
    setTimeout(() => splash.remove(), 900);
  }
  window.addEventListener('load', () => setTimeout(killSplash, 1100));
  setTimeout(killSplash, 4500); // failsafe

  /* ── Header scrolled state ─────────────────────────────────── */
  const header = document.querySelector('.top-header');
  function onScroll() { if (header) header.classList.toggle('scrolled', window.scrollY > 12); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── Cursor glow ───────────────────────────────────────────── */
  const glow = $('cursorGlow');
  if (glow && finePointer && !reduced) {
    let tx = innerWidth / 2, ty = innerHeight / 2, x = tx, y = ty;
    window.addEventListener('mousemove', (e) => { tx = e.clientX; ty = e.clientY; });
    (function loop() {
      x += (tx - x) * 0.12; y += (ty - y) * 0.12;
      glow.style.transform = `translate(${x - 240}px, ${y - 240}px)`;
      requestAnimationFrame(loop);
    })();
  } else if (glow) {
    glow.style.display = 'none';
  }

  /* ── Particle field ────────────────────────────────────────── */
  const canvas = $('particles');
  if (canvas && !reduced) {
    const ctx = canvas.getContext('2d');
    const COLORS = ['rgba(139,92,246,', 'rgba(34,211,238,', 'rgba(52,211,153,', 'rgba(99,102,241,'];
    let w, h, parts = [];

    function resize() { w = canvas.width = innerWidth; h = canvas.height = innerHeight; }
    resize();
    window.addEventListener('resize', resize);

    const N = Math.min(70, Math.floor(innerWidth / 24));
    for (let i = 0; i < N; i++) {
      parts.push({
        x: Math.random() * innerWidth,
        y: Math.random() * innerHeight,
        r: Math.random() * 1.9 + 0.4,
        vy: -(Math.random() * 0.35 + 0.08),
        vx: (Math.random() - 0.5) * 0.2,
        c: COLORS[Math.floor(Math.random() * COLORS.length)] + (Math.random() * 0.5 + 0.25) + ')',
        tw: Math.random() * Math.PI * 2,
      });
    }

    function tick() {
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.y += p.vy; p.x += p.vx; p.tw += 0.02;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        if (p.x < -10) p.x = w + 10; if (p.x > w + 10) p.x = -10;
        ctx.globalAlpha = 0.35 + Math.sin(p.tw) * 0.3;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.c;
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      requestAnimationFrame(tick);
    }
    tick();
  }

  /* ── 3D tilt (delegated so dynamic cards work) ─────────────── */
  if (finePointer && !reduced) {
    const SELECTOR = '.idea-card, .action-card, .domain-card, .stat-card, #heroCard';
    let spinning = false;
    document.addEventListener('mousemove', (e) => {
      if (spinning) return;
      spinning = true;
      requestAnimationFrame(() => {
        const el = e.target.closest ? e.target.closest(SELECTOR) : null;
        if (el) {
          const r = el.getBoundingClientRect();
          const px = (e.clientX - r.left) / r.width - 0.5;
          const py = (e.clientY - r.top) / r.height - 0.5;
          el.style.transform = `perspective(900px) rotateX(${(-py * 6).toFixed(2)}deg) rotateY(${(px * 8).toFixed(2)}deg) translateY(-3px)`;
        }
        spinning = false;
      });
    });
    document.addEventListener('mouseout', (e) => {
      const el = e.target.closest ? e.target.closest(SELECTOR) : null;
      if (el) el.style.transform = '';
    });
  }

  /* ── Hero chip parallax ────────────────────────────────────── */
  const hero = document.querySelector('.hero-container');
  const chips = document.querySelectorAll('.float-chip');
  if (hero && chips.length && finePointer && !reduced) {
    hero.addEventListener('mousemove', (e) => {
      const r = hero.getBoundingClientRect();
      const dx = (e.clientX - r.left) / r.width - 0.5;
      const dy = (e.clientY - r.top) / r.height - 0.5;
      chips.forEach((c, i) => {
        const f = 16 + i * 9;
        c.style.setProperty('--px', (dx * f).toFixed(1) + 'px');
        c.style.setProperty('--py', (dy * f).toFixed(1) + 'px');
      });
    });
  }
})();