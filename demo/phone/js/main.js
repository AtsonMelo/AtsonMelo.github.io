// NUI entry: handshake with Lua, HUD button, phone open/close, failure handling.
import { PROTOCOL, inGame, on, emit, post } from './bridge.js';
import { createPhone } from './phone.js';
import { pad2 } from './format.js';

const $ = (id) => document.getElementById(id);
const body = document.body;
const READY_RETRIES = 6;
const READY_RETRY_MS = 500;
const INIT_TIMEOUT_MS = 10000;
const ALIVE_MS = 5000;

let mode = 'HUD';
let aliveTimer = null;
let initTimer = null;

const phone = createPhone({ screen: $('screen'), back: $('btn-back'), nav: $('nav-top'), backLabel: $('back-label'), islandId: $('island-id') }, { onRetry: retryInit });

// ---- visibility -------------------------------------------------------------------------------
function setMode(next) {
  const wasOpen = mode === 'PHONE';
  mode = next;
  body.dataset.mode = next;
  $('phone').hidden = next !== 'PHONE';
  $('hud-button').setAttribute('aria-label', next === 'CURSOR' ? 'Abrir celular' : 'Celular');
  if (wasOpen && next !== 'PHONE') phone.reset();
  if (next === 'PHONE') phone.render();
  // Heartbeat only while we own focus: Lua force-closes if the page goes silent (docs/phone/09 R-04).
  clearInterval(aliveTimer);
  aliveTimer = next === 'HUD' ? null : setInterval(() => post('phone:alive'), ALIVE_MS);
}

function setStatus(status) {
  clearTimeout(initTimer);
  phone.setStatus(status);
  body.dataset.ready = status === 'connecting' ? 'false' : 'true'; // the button appears once we know the outcome
}

// ---- handshake --------------------------------------------------------------------------------
function sendReady(attempt = 0) {
  post('ready', { protocol: PROTOCOL }).then((res) => {
    if (res && res.ok) return;
    // Lua may not have registered its NUI callbacks yet (resource start race): retry briefly.
    if (attempt < READY_RETRIES) setTimeout(() => sendReady(attempt + 1), READY_RETRY_MS);
    else setStatus('failed');
  });
  clearTimeout(initTimer);
  initTimer = setTimeout(() => { if (phone.status() === 'connecting') setStatus('failed'); }, INIT_TIMEOUT_MS);
}

function retryInit() {
  setStatus('connecting');
  body.dataset.ready = 'true'; // keep the button while retrying; the phone shows "Conectando…"
  post('phone:retryInit').then(() => {
    clearTimeout(initTimer);
    initTimer = setTimeout(() => { if (phone.status() === 'connecting') setStatus('failed'); }, INIT_TIMEOUT_MS);
  });
}

on('init', (d) => {
  if (d.protocol !== PROTOCOL) return setStatus('protocol');
  const hud = (d.config && d.config.hud) || {};
  const off = hud.offset || {};
  const safe = Number(hud.safeZone) > 0 && Number(hud.safeZone) <= 1 ? Number(hud.safeZone) : 1;
  const root = document.documentElement.style;
  root.setProperty('--hud-right', `${(Number(off.right) || 24) + ((1 - safe) / 2) * window.innerWidth}px`);
  root.setProperty('--hud-bottom', `${(Number(off.bottom) || 24) + ((1 - safe) / 2) * window.innerHeight}px`);
  const snap = d.snapshot || {};
  if (snap.device) {
    const pct = Math.max(0, Math.min(100, Number(snap.device.battery) || 0));
    $('battery').textContent = `${pct}%`;
    $('batt-fill').style.setProperty('width', `${pct}%`); // CSSOM: allowed by the CSP
    $('batt').classList.toggle('low', pct < 20);
    $('signal').dataset.level = String(Math.max(0, Math.min(4, Math.ceil((Number(snap.device.signal) || 0) * 4 / 5))));
    $('device-model').textContent = String(snap.device.model || '');
  }
  phone.setIdentity(snap.player, snap.device && snap.device.model);
  phone.setNotifications(snap.notifications);
  setStatus('ready');
  setMode(d.mode || 'HUD');
});

on('init:failed', (d) => setStatus(d.reason === 'PROTOCOL' ? 'protocol' : 'failed'));
on('mode', (d) => { if (d.mode === 'HUD' || d.mode === 'CURSOR' || d.mode === 'PHONE') setMode(d.mode); });
on('hud:visible', (d) => { body.dataset.hud = d.visible ? 'shown' : 'hidden'; });
on('clock', (d) => {
  const text = `${pad2(d.hh)}:${pad2(d.mm)}`;
  $('clock').textContent = text;
  phone.setTime(text);
});
on('shutdown', () => {
  phone.setIdentity(null); body.dataset.ready = 'false'; setMode('HUD'); });

// ---- input --------------------------------------------------------------------------------------
const closePhone = (reason) => post('phone:close', { reason });

$('hud-button').addEventListener('click', () => { if (mode === 'CURSOR') post('phone:openFromButton'); });
$('btn-x').addEventListener('click', () => closePhone('button'));
$('btn-back').addEventListener('click', () => phone.router.back());
$('btn-home').addEventListener('click', () => phone.router.home());

window.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (mode === 'PHONE') { if (phone.escape() === 'close') closePhone('esc'); }
  else if (mode === 'CURSOR') post('phone:cursorExit');
});

let lastTouch = 0;
window.addEventListener('mousemove', () => {
  const now = Date.now();
  if (mode === 'HUD' || now - lastTouch < 500) return;
  lastTouch = now;
  post('phone:touch');
});

// ---- failure containment --------------------------------------------------------------------------
// A script error must never leave the player stuck with a dead, focus-grabbing page.
function fatal(err) {
  console.error('[devlab_phone] uncaught', err);
  if (mode !== 'HUD') closePhone('home');
}
window.addEventListener('error', (e) => fatal(e.error || e.message));
window.addEventListener('unhandledrejection', (e) => fatal(e.reason));

// ---- start ----------------------------------------------------------------------------------------
phone.render();
sendReady();

// Plain-browser preview (no FiveM): fake handshake so the UI can be eyeballed with ?mode=PHONE.
if (!inGame) {
  const q = new URLSearchParams(location.search).get('mode') || 'HUD';
  emit('init', { protocol: PROTOCOL, config: { hud: { offset: { right: 24, bottom: 24 }, safeZone: 1 } },
    snapshot: { player: { id: 1, verified: true }, device: { model: 'DevLab One (preview)', battery: 82 },
      notifications: [{ title: 'Banco', body: 'Pagamento simulado recebido', route: 'bank.home' },
        { title: 'Marina', body: 'Notificação demonstrativa', route: 'msg.list' }] }, mode: q });
}
