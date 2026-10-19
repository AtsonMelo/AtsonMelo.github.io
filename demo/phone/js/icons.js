// Local SVG icons in the Lucide style (24x24, 2px stroke, round caps). Built with createElementNS: no HTML parsing, no assets.
const NS = 'http://www.w3.org/2000/svg';

const ICONS = {
  smartphone: [['rect', { x: 5, y: 2, width: 14, height: 20, rx: 2, ry: 2 }], ['path', { d: 'M12 18h.01' }]],
  car: [
    ['path', { d: 'M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2' }],
    ['circle', { cx: 7, cy: 17, r: 2 }], ['path', { d: 'M9 17h6' }], ['circle', { cx: 17, cy: 17, r: 2 }],
  ],
  message: [['path', { d: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' }]],
  wallet: [
    ['path', { d: 'M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1' }],
    ['path', { d: 'M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4' }],
  ],
  pix: [['path', { d: 'm16 3 4 4-4 4' }], ['path', { d: 'M20 7H4' }], ['path', { d: 'm8 21-4-4 4-4' }], ['path', { d: 'M4 17h16' }]],
  x: [['path', { d: 'M18 6 6 18' }], ['path', { d: 'm6 6 12 12' }]],
  back: [['path', { d: 'm15 18-6-6 6-6' }]],
  home: [
    ['path', { d: 'M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8' }],
    ['path', { d: 'M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' }],
  ],
  send: [['path', { d: 'm22 2-7 20-4-9-9-4Z' }], ['path', { d: 'M22 2 11 13' }]],
  list: [['path', { d: 'M8 6h13' }], ['path', { d: 'M8 12h13' }], ['path', { d: 'M8 18h13' }], ['path', { d: 'M3 6h.01' }], ['path', { d: 'M3 12h.01' }], ['path', { d: 'M3 18h.01' }]],
  check: [['path', { d: 'M20 6 9 17l-5-5' }]],
  chevron: [['path', { d: 'm9 18 6-6-6-6' }]],
};

export function hasIcon(name) {
  return Object.prototype.hasOwnProperty.call(ICONS, name);
}

export function icon(name, size = 24) {
  const svg = document.createElementNS(NS, 'svg');
  const attrs = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
    'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', focusable: 'false' };
  for (const [k, v] of Object.entries(attrs)) svg.setAttribute(k, String(v));
  for (const [tag, a] of ICONS[name] || []) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(a)) node.setAttribute(k, String(v));
    svg.append(node);
  }
  return svg;
}
