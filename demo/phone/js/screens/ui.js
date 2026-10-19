// Reusable view pieces (docs/phone/04-components.md). Pure builders; no state of their own.
import { h } from '../dom.js';
import { icon } from '../icons.js';

/** Large title, like a native app's navigation title. */
export const title = (text) => h('h1', { class: 'screen-title' }, text);

/** Small grey uppercase label above a grouped list. */
export const sectionHeader = (text) => h('h2', { class: 'section-header' }, text);

/** Footnote-style note (used for the "simulation" notices). */
export const banner = (text) => h('p', { class: 'banner', role: 'note' }, text);

/** opts.kind: primary | secondary | ghost | danger. opts.settleMs: ignore clicks right after the screen appears,
 *  so a double click on the previous screen's button cannot land on this one. */
export function button(label, onclick, opts = {}) {
  const b = h('button', { type: 'button', class: `btn btn-${opts.kind || 'primary'}`, disabled: opts.disabled || !!opts.settleMs, onclick }, label);
  if (opts.settleMs && !opts.disabled) setTimeout(() => { b.disabled = false; }, opts.settleMs);
  return b;
}

/** Round avatar with initials on a stable colour. */
export function avatar(name, size = 40) {
  const palette = ['#5e5ce6', '#ff9f0a', '#30d158', '#0a84ff', '#ff453a', '#bf5af2'];
  let sum = 0;
  for (const ch of name) sum += ch.codePointAt(0);
  const el = h('span', { class: 'avatar', 'aria-hidden': 'true' }, name.trim().slice(0, 1).toUpperCase());
  el.style.setProperty('width', `${size}px`);
  el.style.setProperty('height', `${size}px`);
  el.style.setProperty('background', palette[sum % palette.length]);
  return el;
}

/** One row of a grouped list. */
export function listItem({ title: t, sub, meta, onclick, badge, lead }) {
  return h('button', { type: 'button', class: lead ? 'list-item with-lead' : 'list-item', onclick },
    lead || null,
    h('span', { class: 'li-main' }, h('span', { class: 'li-title' }, t), sub ? h('span', { class: 'li-sub' }, sub) : null),
    badge ? h('span', { class: 'dot', 'aria-label': `${badge} não lidas` }) : null,
    meta ? h('span', { class: 'li-meta' }, meta) : null,
    onclick ? icon('chevron', 16) : null);
}

export const group = (...rows) => h('div', { class: 'list' }, rows);

export function meter(label, pct) {
  const fill = h('span', { class: 'meter-fill' });
  fill.style.setProperty('width', `${Math.max(0, Math.min(100, pct))}%`); // CSSOM, allowed by the CSP
  return h('div', { class: 'meter' },
    h('span', { class: 'meter-label' }, label, h('b', null, `${pct}%`)), h('span', { class: 'meter-track' }, fill));
}

export const emptyState = (text) => h('p', { class: 'empty' }, text);
