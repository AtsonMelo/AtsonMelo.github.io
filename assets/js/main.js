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
  var phNodes = [].slice.call(doc.querySelectorAll('[data-i18n-ph]'));
  nodes.forEach(function (n) { n._en = n.innerHTML; });
  altNodes.forEach(function (n) { n._en = n.getAttribute('alt'); });
  phNodes.forEach(function (n) { n._en = n.getAttribute('placeholder'); });

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
    phNodes.forEach(function (n) {
      var v = pt ? PT[n.getAttribute('data-i18n-ph')] : n._en;
      if (v != null) n.setAttribute('placeholder', v);
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
  // Discord entry points exist only when a real invite is configured (never a dead or invented link).
  var hasDiscord = !!cfg.discordUrl;
  [].forEach.call(doc.querySelectorAll('[data-discord]'), function (a) {
    if (hasDiscord) { a.hidden = false; a.href = cfg.discordUrl; a.target = '_blank'; a.rel = 'noopener noreferrer'; }
  });
  doc.getElementById('flow-discord').hidden = !hasDiscord;
  doc.getElementById('flow-generic').hidden = hasDiscord;

  doc.getElementById('year').textContent = new Date().getFullYear();

  // ---- phone demo: iframe is created only on click (no cost until requested) ----
  var launch = doc.getElementById('demo-launch');
  if (launch) launch.addEventListener('click', function () {
    var stage = doc.getElementById('demo-stage');
    var f = doc.createElement('iframe');
    f.className = 'demo-frame';
    f.src = 'demo/phone/index.html';
    f.title = doc.documentElement.lang === 'pt-BR' ? 'Demonstração interativa do DevLab Phone (simulada)' : 'DevLab Phone interactive demo (simulated)';
    // Opaque origin (no allow-same-origin): the demo cannot touch this page's DOM, storage or cookies. It still runs its scripts.
    f.setAttribute('sandbox', 'allow-scripts');
    f.setAttribute('allow', '');
    f.setAttribute('referrerpolicy', 'no-referrer');
    stage.replaceChild(f, stage.querySelector('.demo-poster'));
    f.addEventListener('load', function () { try { f.contentWindow.focus(); } catch (e) { /* ignore */ } });
  });

  // ---- quote form: builds a brief in the browser; nothing is sent or stored ----
  var form = doc.getElementById('quote');
  var LABELS = { resource: 'Custom FiveM resource', nui: 'NUI interface', integration: 'System integration', fix: 'Fix, optimization or maintenance', unsure: 'Not sure yet' };
  var desc = doc.getElementById('q-desc');
  desc.addEventListener('input', function () { doc.getElementById('q-count').textContent = desc.value.length; });
  [].forEach.call(doc.querySelectorAll('[data-service]'), function (a) {
    a.addEventListener('click', function () { doc.getElementById('q-type').value = a.getAttribute('data-service'); });
  });
  function say(el, text) { el.textContent = text; }
  function build(v) {
    return ['FiveM project request (via atsonmelo.github.io)', '',
      'Project type: ' + LABELS[v.type], 'Framework: ' + v.fw, 'Desired feature: ' + (v.feature || '-'), '',
      'Description:', v.desc, '', 'Contact: ' + v.contact].join('\n');
  }
  function copy(text, status) {
    var ok = function () { say(status, doc.documentElement.lang === 'pt-BR' ? 'Briefing copiado.' : 'Brief copied.'); };
    var fail = function () { var t = doc.getElementById('q-brief'); t.focus(); t.select(); say(status, doc.documentElement.lang === 'pt-BR' ? 'Selecione e copie o texto acima (Ctrl+C).' : 'Select and copy the text above (Ctrl+C).'); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, fail); else fail();
  }
  function action(label, href, onclick) {
    var el = doc.createElement(href ? 'a' : 'button');
    el.className = 'btn small'; el.textContent = label;
    if (href) { el.href = href; el.rel = 'noopener'; } else { el.type = 'button'; }
    if (onclick) el.addEventListener('click', onclick);
    return el;
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var err = doc.getElementById('q-error');
    var f = form.elements;
    var v = { type: f.type.value, fw: f.fw.value, feature: f.feature.value.trim(), desc: f.desc.value.trim(), contact: f.contact.value.trim() };
    var pt = doc.documentElement.lang === 'pt-BR';
    var missing = [];
    if (!v.type) missing.push('q-type');
    if (v.desc.length < 20) missing.push('q-desc');
    if (!v.contact) missing.push('q-contact');
    ['q-type', 'q-desc', 'q-contact'].forEach(function (id) { doc.getElementById(id).setAttribute('aria-invalid', missing.indexOf(id) >= 0 ? 'true' : 'false'); });
    if (missing.length) {
      err.hidden = false;
      err.textContent = pt ? 'Preencha o tipo de projeto, uma descrição (mínimo 20 caracteres) e um contato.' : 'Please choose a project type, describe your need (at least 20 characters) and add a way to reach you.';
      doc.getElementById(missing[0]).focus();
      return;
    }
    err.hidden = true;
    var text = build(v);
    doc.getElementById('q-brief').value = text;
    doc.getElementById('brief').hidden = false;
    var box = doc.getElementById('brief-actions'); var status = doc.getElementById('brief-status');
    box.textContent = ''; say(status, pt ? 'Ainda não enviado. Escolha como enviar.' : 'Not sent yet. Choose how to send it.');
    box.appendChild(action(pt ? 'Copiar briefing' : 'Copy brief', null, function () { copy(text, status); }));
    var subject = encodeURIComponent('FiveM project request');
    if (cfg.email) box.appendChild(action(pt ? 'Enviar por e-mail' : 'Send by e-mail', 'mailto:' + cfg.email + '?subject=' + subject + '&body=' + encodeURIComponent(text)));
    if (cfg.discordUrl) box.appendChild(action(pt ? 'Copiar e abrir Discord' : 'Copy and open Discord', cfg.discordUrl, function () { copy(text, status); }));
    if (cfg.issuesRepo) box.appendChild(action(pt ? 'Abrir como issue pública no GitHub' : 'Open as public GitHub issue', 'https://github.com/' + cfg.issuesRepo + '/issues/new?title=' + subject + '&body=' + encodeURIComponent(text)));
    if (cfg.discordUrl) say(status, pt ? 'Briefing pronto, mas NÃO enviado. Copie, entre no Discord e cole em um tópico privado em #solicitar-orcamento.' : 'Brief ready, but NOT sent. Copy it, join Discord and paste it in a private thread in #solicitar-orcamento.');
    if (!cfg.email && !cfg.discordUrl && !cfg.issuesRepo) say(status, pt ? 'Os canais diretos ainda estão sendo configurados. Copie o briefing e envie pelo GitHub.' : 'Direct channels are still being set up. Copy the brief and reach out via GitHub.');
    doc.getElementById('q-brief').scrollIntoView({ block: 'nearest' });
  });

  // ---- reveal on scroll (content stays visible without JS / with reduced motion) ----
  var targets = [].slice.call(doc.querySelectorAll('.card, .svc, .quote, .ev-table, .skills li, .steps li, .section-head, .contact-box, .proof-grid > div'));
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    targets.forEach(function (t) { t.classList.add('reveal'); io.observe(t); });
  }
})();
