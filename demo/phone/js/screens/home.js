import { h } from '../dom.js';
import { icon } from '../icons.js';
import { bank, contacts } from '../data.js';
import { money } from '../format.js';

// The real apps live in the dock, like a phone with widgets on its home page.
const APPS = [
  { id: 'vehicles', label: 'Veículos', icon: 'car', route: 'veh.list' },
  { id: 'messages', label: 'Mensagens', icon: 'message', route: 'msg.list' },
  { id: 'bank', label: 'Banco', icon: 'wallet', route: 'bank.home' },
  { id: 'pix', label: 'PIX', icon: 'pix', route: 'bank.pix' },
];

const KINDS = {
  bank: { key: 'bank', icon: 'wallet', label: 'Banco' },
  msg: { key: 'msg', icon: 'message', label: 'Mensagens' },
  veh: { key: 'veh', icon: 'car', label: 'Veículos' },
};
const DOW = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
const MONTH = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function notifKind(route) {
  const prefix = typeof route === 'string' ? route.split('.')[0] : '';
  return KINDS[prefix] || KINDS.msg;
}

export function home(_param, ctx) {
  const unread = contacts.reduce((n, c) => n + c.unread, 0);
  const now = new Date();

  const myId = ctx.player ? `Meu ID: ${ctx.player.id}` : 'Meu ID: indisponível';
  const today = h('button', { type: 'button', class: 'widget widget-today', 'aria-label': 'Perfil', onclick: () => ctx.router.push('profile') },
    h('span', { class: 'w-date' }, h('span', { class: 'w-dow' }, DOW[now.getDay()]), h('span', { class: 'w-day' }, `${now.getDate()} de ${MONTH[now.getMonth()]}`),
      h('span', { class: 'w-id', 'data-testid': 'my-id' }, myId)),
    h('span', { class: 'w-time', 'data-testid': 'w-time' }, ctx.time || '--:--'));

  const rows = ctx.notifications.slice(0, 3).map((n) => {
    const kind = notifKind(n.route);
    return h('button', { type: 'button', class: 'notif', 'data-testid': 'notif', onclick: () => { if (n.route) ctx.router.push(n.route); } },
      h('span', { class: 'notif-glyph', 'data-kind': kind.key }, icon(kind.icon, 16)),
      h('span', { class: 'notif-text' }, h('span', { class: 'notif-title' }, n.title), h('span', { class: 'notif-body' }, n.body)),
      h('span', { class: 'notif-time' }, 'agora'));
  });
  const notifs = h('div', { class: 'widget widget-notifs' }, h('h2', { class: 'w-header' }, 'Notificações'),
    rows.length ? rows : h('p', { class: 'w-empty' }, 'Nenhuma notificação'));

  const small = (cls, route, glyph, kind, label, big, sub) => h('button', { type: 'button', class: `widget widget-small ${cls}`, onclick: () => ctx.router.push(route) },
    h('span', { class: 'ws-head' }, h('span', { class: 'notif-glyph', 'data-kind': kind }, icon(glyph, 16)), h('span', { class: 'ws-label' }, label)),
    h('span', { class: 'ws-big' }, big), h('span', { class: 'ws-sub' }, sub));
  const widgetsRow = h('div', { class: 'widgets-row' },
    small('widget-bank', 'bank.home', 'wallet', 'bank', 'Banco', money(bank.balanceCents), 'Saldo disponível'),
    small('widget-veh', 'veh.list', 'car', 'veh', 'Veículos', 'Bugatti Chiron', 'Toque para chamar'));

  const tiles = APPS.map((app) => h('button', { type: 'button', class: 'app-tile', 'data-app': app.id, title: app.label,
    'aria-label': app.label, onclick: () => ctx.router.push(app.route) },
  h('span', { class: 'app-icon' }, icon(app.icon, 28), app.id === 'messages' && unread > 0 ? h('span', { class: 'badge badge-abs' }, unread) : null),
  h('span', { class: 'app-label' }, app.label)));

  return { el: h('section', { class: 'screen home' }, today, notifs, widgetsRow,
    h('div', { class: 'page-dots', 'aria-hidden': 'true' }, h('i', { class: 'on' }), h('i')),
    h('div', { class: 'dock' }, tiles)) };
}
