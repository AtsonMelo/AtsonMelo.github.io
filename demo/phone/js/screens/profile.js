// Profile / device info. The id shown here is the SERVER id confirmed by the server (never a value typed by the user).
import { h } from '../dom.js';
import { banner, button, group, title } from './ui.js';

/** Clipboard with a fallback: the CEF used by FiveM does not always expose navigator.clipboard. */
export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch { /* fall through to the legacy path */ }
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.setProperty('position', 'fixed');
    ta.style.setProperty('opacity', '0');
    document.body.append(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  } catch {
    return false;
  }
}

export function profile(_param, ctx) {
  const p = ctx.player;
  const ready = !!(p && p.verified && Number.isInteger(p.id));
  const status = h('p', { class: 'footnote', role: 'status', 'data-testid': 'copy-status' });
  const line = (k, v, testid) => h('div', { class: 'cell' }, h('span', { class: 'li-title' }, k),
    h('span', { class: 'li-meta push', 'data-testid': testid }, v));

  async function copy() {
    const ok = await copyText(String(p.id));
    status.className = `footnote ${ok ? 'ok' : 'err'}`;
    status.textContent = ok ? 'ID copiado.' : 'Não foi possível copiar. Anote o ID manualmente.';
  }

  return { el: h('section', { class: 'screen' }, title('Perfil'),
    h('p', { class: 'muted' }, ready ? `${ctx.deviceModel || 'DevLab One'} | ID: ${p.id}` : `${ctx.deviceModel || 'DevLab One'} | ID indisponível`),
    group(line('Dispositivo', ctx.deviceModel || 'DevLab One'), line('Meu ID', ready ? String(p.id) : 'Indisponível', 'profile-id')),
    button('Copiar ID', copy, { kind: 'secondary', disabled: !ready }), status,
    banner('O ID identifica esta conexão no servidor. Ele muda se você reconectar e pode ser reutilizado por outro jogador depois de uma desconexão: não é um identificador permanente.')) };
}
