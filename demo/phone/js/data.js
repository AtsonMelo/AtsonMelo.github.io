// Demonstrative data (visual-only stage). Nothing here is persisted or sent anywhere.
// Real data arrives through the NUI/Lua contracts in later stages (docs/phone/05-contracts.md).
export const vehicles = [
  { id: 'v1', name: 'Sultan RS', plate: 'DLT1A23', state: 'stored', fuel: 78, engine: 100, body: 92 },
  { id: 'v2', name: 'Kuruma', plate: 'DLT2B34', state: 'stored', fuel: 45, engine: 96, body: 70 },
  { id: 'v3', name: 'Faggio', plate: 'DLT3C45', state: 'out', fuel: 60, engine: 88, body: 81 },
];

export const contacts = [
  { id: 'marina', name: 'Marina', unread: 1, history: [
    { from: 'them', text: 'Oi! Esta é uma conversa demonstrativa.' },
    { from: 'me', text: 'Tudo certo por aqui.' },
    { from: 'them', text: 'Quando puder, me chama.' } ] },
  { id: 'carlos', name: 'Carlos', unread: 0, history: [{ from: 'them', text: 'Passa na oficina depois.' }] },
  { id: 'oficina', name: 'Oficina Central', unread: 0, history: [{ from: 'them', text: 'Seu veículo está pronto (demo).' }] },
];

export const pixDirectory = [
  { key: 'DL-0001', name: 'Marina Souza' },
  { key: 'DL-0002', name: 'Carlos Lima' },
  { key: 'dl-oficina-01', name: 'Oficina Central' },
];

// Session-only state: resets when the page reloads. Entries sum to balanceCents.
export const bank = {
  balanceCents: 1250000,
  entries: [
    { id: 'e3', label: 'Pagamento recebido (demo)', cents: 45000, when: 'Hoje' },
    { id: 'e2', label: 'Combustível (demo)', cents: -8990, when: 'Ontem' },
    { id: 'e1', label: 'Saldo inicial de simulação', cents: 1213990, when: 'Seg' },
  ],
};

export const LIMITS = { pixMaxCents: 500000, messageMax: 280 };
