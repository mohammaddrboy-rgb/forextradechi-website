/* مکتب فارکس — Maktab Forex | shared site behaviour. Vanilla JS, no dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;

  /* ---- Language switch (English primary, Farsi secondary) ---- */
  function applyLang(lang) {
    lang = (lang === 'fa') ? 'fa' : 'en';
    root.lang = lang;
    root.dir = (lang === 'fa') ? 'rtl' : 'ltr';
    // Page <title> per language (stored on <html data-title-en / data-title-fa>)
    var t = root.getAttribute('data-title-' + lang);
    if (t) document.title = t;
    // Toggle button shows the OTHER language it will switch to
    document.querySelectorAll('.lang-toggle .lt-label').forEach(function (el) {
      el.textContent = (lang === 'fa') ? 'EN' : 'فارسی';
    });
    document.querySelectorAll('.lang-toggle').forEach(function (b) {
      b.setAttribute('aria-label', lang === 'fa' ? 'Switch to English' : 'تغییر به فارسی');
    });
    try { localStorage.setItem('mf-lang', lang); } catch (e) {}
    // Direction may have flipped — let direction-aware widgets (carousel) re-measure.
    window.dispatchEvent(new Event('resize'));
  }

  // Language is determined by the URL: /fa/… is Farsi, everything else is English.
  var isFa = location.pathname.indexOf('/fa/') !== -1;
  applyLang(isFa ? 'fa' : 'en');

  // The toggle is a real language switch: it navigates to the alternate-language URL,
  // so each language has its own shareable, indexable address.
  document.querySelectorAll('.lang-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var p = location.pathname, target;
      if (isFa) {
        target = p.replace('/fa/', '/');
      } else {
        target = '/fa' + ((p === '/' || p === '') ? '/index.html' : p);
      }
      window.location.href = target + location.hash;
    });
  });

  /* ---- Sticky nav shadow on scroll ---- */
  var nav = document.querySelector('.nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---- Mobile menu ---- */
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  var backdrop = document.querySelector('.nav-backdrop');

  function setMenu(open) {
    if (!links || !toggle) return;
    links.classList.toggle('open', open);
    if (backdrop) backdrop.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.classList.toggle('menu-open', open);
  }

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      setMenu(!links.classList.contains('open'));
    });
    if (backdrop) backdrop.addEventListener('click', function () { setMenu(false); });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setMenu(false);
    });
  }

  /* ---- Accordion (advanced course modules) ---- */
  document.querySelectorAll('.acc-head').forEach(function (head) {
    head.addEventListener('click', function () {
      var panel = head.nextElementSibling;
      var open = head.getAttribute('aria-expanded') === 'true';
      head.setAttribute('aria-expanded', open ? 'false' : 'true');
      if (panel) panel.style.maxHeight = open ? null : panel.scrollHeight + 'px';
    });
  });

  /* ---- Testimonial avatars (initial letter from the active-language name) ---- */
  function updateAvatars() {
    var lang = document.documentElement.lang === 'fa' ? 'fa' : 'en';
    document.querySelectorAll('.testimonial .who').forEach(function (who) {
      var av = who.querySelector('.t-avatar');
      if (!av) return;
      var name = who.querySelector('.lang-' + lang) || who.querySelector('.lang-en');
      av.textContent = name ? name.textContent.trim().charAt(0) : '★';
    });
  }
  document.querySelectorAll('.testimonial .who').forEach(function (who) {
    if (who.querySelector('.t-avatar')) return;
    var av = document.createElement('span');
    av.className = 't-avatar';
    av.setAttribute('aria-hidden', 'true');
    who.classList.add('has-avatar');
    who.insertBefore(av, who.firstChild);
  });
  updateAvatars();
  window.addEventListener('resize', updateAvatars);   /* also fires on language toggle */

  /* ---- Carousel (testimonials) — transform-based, arrows + dots + swipe, RTL-aware ---- */
  function initCarousel(root) {
    var viewport = root.querySelector('.carousel-viewport');
    var track = root.querySelector('.carousel-track');
    if (!viewport || !track) return;
    var cards = Array.prototype.slice.call(track.children);
    if (!cards.length) return;
    var prev = root.querySelector('.carousel-btn.prev');
    var next = root.querySelector('.carousel-btn.next');
    var dotsWrap = root.querySelector('.carousel-dots');
    var index = 0, dots = [];

    var offsets = [];   // each card's start-edge position (relative to viewport) at translateX(0)

    function rtl() { return getComputedStyle(track).direction === 'rtl'; }
    function startEdge(r) { return rtl() ? r.right : r.left; }
    function step() {
      var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return cards[0].getBoundingClientRect().width + gap;
    }
    function perView() { return Math.max(1, Math.round(viewport.clientWidth / step())); }
    function maxIndex() { return Math.max(0, cards.length - perView()); }

    function measure() {
      var pt = track.style.transition, px = track.style.transform;
      track.style.transition = 'none';
      track.style.transform = 'translateX(0px)';
      var vs = startEdge(viewport.getBoundingClientRect());
      offsets = cards.map(function (c) { return startEdge(c.getBoundingClientRect()) - vs; });
      track.style.transform = px;
      void track.offsetWidth;            // reflow so the restored transition doesn't animate the reset
      track.style.transition = pt;
    }

    function buildDots() {
      if (!dotsWrap) return;
      var positions = maxIndex() + 1;
      dotsWrap.innerHTML = '';
      dots = [];
      for (var i = 0; i < positions; i++) {
        (function (p) {
          var b = document.createElement('button');
          b.type = 'button';
          b.setAttribute('aria-label', 'Go to slide ' + (p + 1));
          b.addEventListener('click', function () { index = p; apply(); });
          dotsWrap.appendChild(b);
          dots.push(b);
        })(i);
      }
    }
    function apply() {
      index = Math.min(maxIndex(), Math.max(0, index));
      track.style.transform = 'translateX(' + (-offsets[index]) + 'px)';
      if (prev) prev.disabled = index <= 0;
      if (next) next.disabled = index >= maxIndex();
      dots.forEach(function (d, di) { d.classList.toggle('active', di === index); });
    }
    function go(delta) { index += delta; apply(); }

    if (prev) prev.addEventListener('click', function () { go(-perView()); });
    if (next) next.addEventListener('click', function () { go(perView()); });

    // Touch swipe
    var x0 = null;
    track.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    track.addEventListener('touchend', function (e) {
      if (x0 == null) return;
      var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) < 40) return;
      var forward = rtl() ? dx > 0 : dx < 0;
      go(forward ? perView() : -perView());
    }, { passive: true });

    function refresh() { measure(); buildDots(); apply(); }
    var t;
    window.addEventListener('resize', function () {
      clearTimeout(t);
      t = setTimeout(refresh, 150);
    });
    // Fonts/images can shift card widths after first paint — re-measure once loaded.
    window.addEventListener('load', refresh);

    refresh();
  }
  document.querySelectorAll('[data-carousel]').forEach(initCarousel);
})();
