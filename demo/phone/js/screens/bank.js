import { h } from '../dom.js';
import { icon } from '../icons.js';
import { bank, pixDirectory, LIMITS } from '../data.js';
import { money, parseMoney } from '../format.js';
import { avatar, banner, button, group, sectionHeader, title } from './ui.js';

const SIM = 'SIMULAÇÃO — valores fictícios, sem movimentação real.';
let draft = null; // { key, name, cents } between the PIX form, review and result screens
let receiptSeq = 0;

function entryRow(e) {
  return h('div', { class: 'row' },
    h('span', { class: 'li-main' }, h('span', { class: 'li-title' }, e.label), h('span', { class: 'li-sub' }, e.when)),
    h('b', { class: e.cents < 0 ? 'neg' : 'pos' }, money(e.cents)));
}

function quick(label, iconName, onclick) {
  return h('button', { type: 'button', class: 'quick', onclick }, h('span', { class: 'quick-icon' }, icon(iconName, 22)), h('span', { class: 'quick-label' }, label));
}

export function bankHome(_param, ctx) {
  return { el: h('section', { class: 'screen' }, title('Banco'),
    h('div', { class: 'balance', 'data-testid': 'balance' }, h('span', { class: 'muted' }, 'Saldo disponível'), h('b', null, money(bank.balanceCents))),
    h('div', { class: 'quick-row' }, quick('Extrato', 'list', () => ctx.router.push('bank.statement')), quick('PIX', 'pix', () => ctx.router.push('bank.pix'))),
    sectionHeader('Últimas movimentações'), group(...bank.entries.slice(0, 3).map(entryRow)), banner(SIM)) };
}

export function bankStatement() {
  return { el: h('section', { class: 'screen' }, title('Extrato'), group(...bank.entries.map(entryRow)), banner(SIM)) };
}

export function pixForm(_param, ctx) {
  const error = h('p', { class: 'error', role: 'alert', 'data-testid': 'pix-error' });
  const key = h('input', { type: 'text', class: 'cell-input', 'aria-label': 'Chave PIX ou ID interno', placeholder: 'DL-0001', maxlength: 48, autocomplete: 'off' });
  const amount = h('input', { type: 'text', class: 'cell-input', 'aria-label': 'Valor', placeholder: '0,00', inputmode: 'decimal', maxlength: 14, autocomplete: 'off' });
  if (draft) { key.value = draft.key; amount.value = draft.raw || ''; }

  const people = pixDirectory.map((p) => h('button', { type: 'button', class: 'person', onclick: () => { key.value = p.key; } },
    avatar(p.name, 46), h('span', null, p.name.split(' ')[0])));

  function review() {
    const dest = pixDirectory.find((p) => p.key === key.value.trim());
    const cents = parseMoney(amount.value);
    let msg = '';
    if (!dest) msg = 'Chave não encontrada.';
    else if (cents === null || cents < 1) msg = 'Informe um valor válido.';
    else if (cents > LIMITS.pixMaxCents) msg = `Limite por operação: ${money(LIMITS.pixMaxCents)}.`;
    else if (cents > bank.balanceCents) msg = 'Saldo insuficiente.';
    error.textContent = msg;
    if (msg) return;
    draft = { key: dest.key, name: dest.name, cents, raw: amount.value, confirmed: false };
    ctx.router.push('bank.pix.review');
  }

  return { el: h('section', { class: 'screen' }, title('PIX'),
    sectionHeader('Contatos'), h('div', { class: 'people' }, people),
    group(h('label', { class: 'cell' }, h('span', { class: 'cell-label' }, 'Chave'), key),
      h('label', { class: 'cell' }, h('span', { class: 'cell-label' }, 'Valor'), amount)),
    error, button('Continuar', review), banner(SIM)) };
}

export function pixReview(_param, ctx) {
  if (!draft) return { el: h('section', { class: 'screen' }, title('PIX'), h('p', { class: 'muted' }, 'Nada para revisar.')) };
  function confirm() {
    if (draft.confirmed) return; // double click / repeated Enter: debit exactly once
    draft.confirmed = true;
    bank.balanceCents -= draft.cents;
    receiptSeq += 1;
    const receipt = { id: `SIM-${String(receiptSeq).padStart(4, '0')}`, name: draft.name, key: draft.key, cents: draft.cents };
    bank.entries.unshift({ id: receipt.id, label: `PIX para ${draft.name} (demo)`, cents: -draft.cents, when: 'Agora' });
    draft = { receipt };
    ctx.router.replace('bank.pix.result');
  }
  const line = (k, v) => h('div', { class: 'cell' }, h('span', { class: 'li-title' }, k), h('b', { class: 'li-meta push' }, v));
  return { el: h('section', { class: 'screen' }, title('Revisar'),
    h('div', { class: 'list summary' }, line('Para', draft.name), line('Chave', draft.key), line('Valor', money(draft.cents))),
    banner(SIM), button('Confirmar', confirm), button('Voltar', () => ctx.router.back(), { kind: 'ghost' })) };
}

export function pixResult(_param, ctx) {
  const r = draft && draft.receipt;
  if (!r) return { el: h('section', { class: 'screen' }, title('PIX'), h('p', { class: 'muted' }, 'Sem comprovante.')) };
  draft = null;
  const line = (k, v) => h('div', { class: 'cell' }, h('span', { class: 'li-title' }, k), h('span', { class: 'li-meta push' }, v));
  return { el: h('section', { class: 'screen center' },
    h('span', { class: 'done-icon' }, icon('check', 30)), h('h1', { class: 'screen-title' }, 'Concluído'),
    h('div', { class: 'list receipt', 'data-testid': 'receipt' },
      h('div', { class: 'cell' }, h('b', { class: 'receipt-title' }, 'COMPROVANTE DE SIMULAÇÃO')),
      line('Id', r.id), line('Para', `${r.name} (${r.key})`), line('Valor', money(r.cents)), line('Novo saldo', money(bank.balanceCents))),
    h('p', { class: 'footnote' }, 'Nenhum valor real foi movimentado.'),
    button('Concluir', () => ctx.router.home(), { settleMs: 500 })) };
}
