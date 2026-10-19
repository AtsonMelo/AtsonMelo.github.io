// Money is integer cents (fictional BRL). Same rules as lib/money.lua.
export function money(cents) {
  if (!Number.isInteger(cents)) throw new TypeError('cents must be an integer');
  const neg = cents < 0;
  const abs = Math.abs(cents);
  const int = String(Math.floor(abs / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${neg ? '-' : ''}R$ ${int},${String(abs % 100).padStart(2, '0')}`;
}

/** "1.234,56" / "12,5" / "R$ 10" -> integer cents, or null when invalid. */
export function parseMoney(text) {
  if (typeof text !== 'string' || text.length > 24) return null;
  const s = text.replace(/^\s*R\$\s*/, '').trim();
  const m = /^(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$/.exec(s);
  if (!m) return null;
  const int = m[1].replace(/\./g, '');
  if (int.length > 12) return null;
  return Number(int) * 100 + Number(((m[2] || '') + '00').slice(0, 2));
}

export function pad2(n) {
  return String(n).padStart(2, '0');
}
