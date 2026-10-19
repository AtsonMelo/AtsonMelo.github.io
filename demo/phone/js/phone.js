// Phone shell controller: route stack -> screen, connection states, ESC semantics, timer cleanup.
import { clear } from './dom.js';
import { request } from './bridge.js';
import { createRouter, parseRoute } from './router.js';
import { home } from './screens/home.js';
import { vehicleList, vehicleDetail, vehicleCall } from './screens/vehicles.js';
import { messageList, messageThread } from './screens/messages.js';
import { bankHome, bankStatement, pixForm, pixReview, pixResult } from './screens/bank.js';
import { systemScreen } from './screens/system.js';
import { profile } from './screens/profile.js';

const ROUTES = {
  home,
  'veh.list': vehicleList, 'veh.detail': vehicleDetail, 'veh.call': vehicleCall,
  'msg.list': messageList, 'msg.thread': messageThread,
  'bank.home': bankHome, 'bank.statement': bankStatement,
  profile,
  'bank.pix': pixForm, 'bank.pix.review': pixReview, 'bank.pix.result': pixResult,
};

const TITLES = {
  home: 'Início', profile: 'Perfil', 'veh.list': 'Veículos', 'veh.detail': 'Veículos', 'veh.call': 'Veículos',
  'msg.list': 'Mensagens', 'msg.thread': 'Mensagens',
  'bank.home': 'Banco', 'bank.statement': 'Banco', 'bank.pix': 'PIX', 'bank.pix.review': 'PIX', 'bank.pix.result': 'PIX',
};

/**
 * @param {{ screen: HTMLElement, back: HTMLButtonElement, nav: HTMLElement, backLabel: HTMLElement, islandId: HTMLElement }} els
 * @param {{ onRetry: () => void }} deps
 */
export function createPhone(els, deps) {
  let status = 'connecting'; // connecting | ready | failed | protocol
  let notifications = [];
  let cleanup = null;

  const ctx = { notifications, router: null, request, time: '', player: null, deviceModel: '' };
  const router = createRouter(Object.keys(ROUTES), () => render());
  ctx.router = router;

  function release() {
    if (cleanup) { try { cleanup(); } catch { /* a failing cleanup must not block navigation */ } }
    cleanup = null;
  }

  function show(node) {
    clear(els.screen);
    els.screen.append(node);
    els.screen.scrollTop = 0;
  }

  function render() {
    release();
    els.back.disabled = status === 'ready' ? !router.canBack() : true;
    const onHome = status === 'ready' && parseRoute(router.current()).name === 'home';
    els.screen.parentElement.dataset.view = onHome ? 'home' : 'app';
    // native-style back button: shows the title of the screen we came from
    els.nav.hidden = onHome || status !== 'ready';
    const prev = router.previous();
    els.backLabel.textContent = (prev && TITLES[parseRoute(prev).name]) || 'Voltar';
    if (status !== 'ready') return show(systemScreen(status, deps.onRetry));
    try {
      const { name, param } = parseRoute(router.current());
      const view = ROUTES[name](param, ctx);
      cleanup = view.cleanup || null;
      show(view.el);
    } catch (err) {
      console.error('[devlab_phone] screen failed', err);
      show(systemScreen('error', () => router.home() || render()));
    }
  }

  return {
    router,
    status: () => status,
    setStatus(next) { status = next; render(); },
    setNotifications(list) {
      notifications = Array.isArray(list) ? list.filter((n) => n && typeof n.title === 'string' && typeof n.body === 'string').slice(0, 5) : [];
      ctx.notifications = notifications;
    },
    /** Back to a clean home (called when the phone closes). */
    reset() { release(); if (!router.home()) render(); },
    render,
    /** Server-confirmed identity. Anything not verified by the server is shown as unavailable. */
    setIdentity(player, deviceModel) {
      const ok = !!(player && player.verified === true && Number.isInteger(player.id));
      ctx.player = ok ? { id: player.id, verified: true } : null;
      ctx.deviceModel = typeof deviceModel === 'string' ? deviceModel : ctx.deviceModel;
      els.islandId.textContent = ok ? `ID ${player.id}` : 'ID —';
      const el = els.screen.querySelector('[data-testid=my-id]');
      if (el) el.textContent = ok ? `Meu ID: ${player.id}` : 'Meu ID: indisponível';
    },
    /** Latest clock text from Lua (home widget). */
    setTime(text) {
      ctx.time = text;
      const el = els.screen.querySelector('[data-testid=w-time]');
      if (el) el.textContent = text;
    },
    /** ESC: blur field -> back -> close (docs/phone/02 §3). */
    escape() {
      const a = document.activeElement;
      if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) { a.blur(); return 'blur'; }
      if (status === 'ready' && router.back()) return 'back';
      return 'close';
    },
  };
}
