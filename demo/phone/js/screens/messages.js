import { h } from '../dom.js';
import { icon } from '../icons.js';
import { contacts, LIMITS } from '../data.js';
import { avatar, emptyState, group, listItem, title } from './ui.js';

const REPLY_MS = 1200;

export function messageList(_param, ctx) {
  const items = contacts.map((c) => {
    const last = c.history[c.history.length - 1];
    return listItem({ title: c.name, sub: last ? last.text : '', badge: c.unread > 0 ? c.unread : null, meta: 'agora', lead: avatar(c.name, 42),
      onclick: () => { c.unread = 0; ctx.router.push(`msg.thread/${c.id}`); } });
  });
  return { el: h('section', { class: 'screen' }, title('Mensagens'), group(...items)) };
}

/** Demonstrative chat: messages live in memory only; the "reply" is canned and labelled. */
export function messageThread(id) {
  const c = contacts.find((x) => x.id === id);
  if (!c) return { el: h('section', { class: 'screen' }, title('Conversa'), emptyState('Conversa não encontrada.')) };
  const log = h('div', { class: 'chat', 'data-testid': 'chat' });
  let timer = null;
  let sending = false;

  const bubble = (m) => h('div', { class: `bubble ${m.from === 'me' ? 'me' : 'them'}` }, m.text, m.demo ? h('small', null, 'resposta automática (demo)') : null);
  const paint = () => { log.replaceChildren(...c.history.map(bubble)); log.scrollTop = log.scrollHeight; };

  const input = h('input', { type: 'text', class: 'field', maxlength: LIMITS.messageMax, placeholder: 'Mensagem', 'aria-label': 'Mensagem', autocomplete: 'off' });
  const sendBtn = h('button', { type: 'button', class: 'send', 'aria-label': 'Enviar' }, icon('send', 16));

  function send() {
    const text = input.value;
    if (sending || !text.trim() || text.length > LIMITS.messageMax) return;
    sending = true; // one intent = one message, even with repeated Enter
    sendBtn.disabled = true;
    c.history.push({ from: 'me', text });
    input.value = '';
    paint();
    timer = setTimeout(() => {
      c.history.push({ from: 'them', text: 'Recebido! (resposta demonstrativa)', demo: true });
      sending = false;
      sendBtn.disabled = false;
      paint();
    }, REPLY_MS);
  }
  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); send(); } });

  paint();
  return { el: h('section', { class: 'screen thread' },
    h('div', { class: 'thread-head' }, avatar(c.name, 44), h('span', { class: 'thread-name' }, c.name)),
    log, h('div', { class: 'composer' }, input, sendBtn)),
  cleanup: () => { if (timer) clearTimeout(timer); } };
}
