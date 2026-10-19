(function () {
  'use strict';
  var doc = document;
  var cfg = window.SITE_CONFIG || {};
  var PT = window.I18N_PT || {};
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
  };

  // ---- i18n: EN is the static HTML; PT is swapped in from the dictionary ----
  var nodes = [].slice.call(doc.querySelectorAll('[data-i18n]'));
  var altNodes = [].slice.call(doc.querySelectorAll('[data-i18n-alt]'));
  nodes.forEach(function (n) { n._en = n.innerHTML; });
  altNodes.forEach(function (n) { n._en = n.getAttribute('alt'); });

  function setLang(lang) {
    var pt = lang === 'pt';
    // Dictionary strings are authored here (never user input); a few contain <code> markup.
    nodes.forEach(function (n) {
      var v = pt ? PT[n.getAttribute('data-i18n')] : n._en;
      if (v != null) n.innerHTML = v;
    });
    altNodes.forEach(function (n) {
      var v = pt ? PT[n.getAttribute('data-i18n-alt')] : n._en;
      if (v != null) n.setAttribute('alt', v);
    });
    doc.documentElement.lang = pt ? 'pt-BR' : 'en';
    var btn = doc.getElementById('lang');
    btn.setAttribute('data-lang', pt ? 'pt' : 'en');
    store.set('lang', pt ? 'pt' : 'en');
  }
  doc.getElementById('lang').addEventListener('click', function () {
    setLang(this.getAttribute('data-lang') === 'en' ? 'pt' : 'en');
  });
  var saved = store.get('lang');
  var nav = (navigator.language || '').toLowerCase();
  if (saved === 'pt' || (!saved && nav.indexOf('pt') === 0)) setLang('pt');

  // ---- mobile menu ----
  var burger = doc.getElementById('burger');
  var menu = doc.getElementById('nav');
  function closeMenu() { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); }
  burger.addEventListener('click', function () {
    var open = menu.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
  });
  menu.addEventListener('click', function (e) { if (e.target.tagName === 'A') closeMenu(); });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

  // ---- project detail dialogs ----
  doc.addEventListener('click', function (e) {
    var open = e.target.closest('[data-open]');
    if (open) {
      var d = doc.getElementById(open.getAttribute('data-open'));
      if (d && d.showModal) d.showModal();
      return;
    }
    if (e.target.closest('[data-close]')) { e.target.closest('dialog').close(); return; }
    if (e.target.tagName === 'DIALOG') e.target.close(); // backdrop click
  });

  // ---- contact channels from config (nothing invented: empty = not rendered) ----
  var list = doc.getElementById('channels');
  function channel(label, value, href) {
    var li = doc.createElement('li');
    var el = doc.createElement(href ? 'a' : 'div');
    if (href) { el.href = href; if (href.indexOf('http') === 0) el.rel = 'noopener'; } else { el.className = 'static'; }
    var left = doc.createElement('span');
    var small = doc.createElement('small'); small.textContent = label;
    var b = doc.createElement('b'); b.textContent = value;
    left.appendChild(small); left.appendChild(b);
    el.appendChild(left);
    if (href) { var ar = doc.createElement('span'); ar.setAttribute('aria-hidden', 'true'); ar.textContent = '↗'; el.appendChild(ar); }
    li.appendChild(el); list.appendChild(li);
  }
  var direct = 0;
  if (cfg.discordUrl || cfg.discordHandle) { channel('Discord', cfg.discordHandle || cfg.discordUrl.replace(/^https?:\/\//, ''), cfg.discordUrl || ''); direct++; }
  if (cfg.email) { channel('E-mail', cfg.email, 'mailto:' + cfg.email); direct++; }
  if (cfg.github) {
    channel('GitHub', cfg.github.replace(/^https?:\/\/(www\.)?github\.com\//, '@'), cfg.github);
    [].forEach.call(doc.querySelectorAll('[data-github]'), function (a) { a.href = cfg.github; });
  }
  if (!direct) doc.getElementById('channels-note').hidden = false;

  doc.getElementById('year').textContent = new Date().getFullYear();

  // ---- reveal on scroll (content stays visible without JS / with reduced motion) ----
  var targets = [].slice.call(doc.querySelectorAll('.card, .skills li, .steps li, .section-head, .contact-box, .proof-grid > div'));
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    targets.forEach(function (t) { t.classList.add('reveal'); io.observe(t); });
  }
})();
