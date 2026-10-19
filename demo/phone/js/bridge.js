// NUI <-> Lua transport (docs/phone/05-contracts.md). Outside the game (plain browser) it degrades to a no-op mock.
export const PROTOCOL = 1;
export const inGame = typeof GetParentResourceName === 'function';
const RES = inGame ? GetParentResourceName() : 'devlab_phone';
const SAFETY_TIMEOUT_MS = 12000; // Lua synthesizes TIMEOUT at 8 s; this only guards a dead channel

export function post(name, data = {}) {
  if (!inGame) return Promise.resolve({ ok: true, mock: true });
  return fetch(`https://${RES}/${name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=UTF-8' },
    body: JSON.stringify(data),
  }).then((r) => r.json()).catch(() => ({ ok: false }));
}

const listeners = new Map();
export function on(action, fn) {
  if (!listeners.has(action)) listeners.set(action, []);
  listeners.get(action).push(fn);
}
export function emit(action, data) {
  for (const fn of listeners.get(action) || []) fn(data);
}

window.addEventListener('message', (e) => {
  const m = e.data;
  if (!m || m.v !== PROTOCOL || typeof m.action !== 'string') return;
  emit(m.action, m.data || {});
});

const pending = new Map(); // requestId -> { resolve, reject, timer }
let counter = 0;

on('rpc:result', (res) => {
  const p = pending.get(res.requestId);
  if (!p) return;
  clearTimeout(p.timer);
  pending.delete(res.requestId);
  res.ok ? p.resolve(res) : p.reject(res);
});

function settleLocal(rid, code) {
  const p = pending.get(rid);
  if (!p) return;
  clearTimeout(p.timer);
  pending.delete(rid);
  p.reject({ requestId: rid, ok: false, error: { code } });
}

/** One user intent = one requestId. Use retry(rid) to re-send the same id after TIMEOUT. */
export function request(op, args = {}) {
  const rid = `u${++counter}-${Date.now().toString(36)}`.slice(0, 32);
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => settleLocal(rid, 'TIMEOUT'), SAFETY_TIMEOUT_MS);
    pending.set(rid, { resolve, reject, timer });
    post('rpc', { requestId: rid, op, args }).then((r) => {
      if (!r || r.accepted !== true) settleLocal(rid, (r && r.code) || 'INTERNAL');
    });
  });
}

export function retry(rid) {
  return post('rpc:retry', { requestId: rid });
}
