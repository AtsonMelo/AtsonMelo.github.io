import { h } from '../dom.js';
import { icon } from '../icons.js';
import { post } from '../bridge.js';
import { vehicles } from '../data.js';
import { banner, button, emptyState, group, listItem, meter, sectionHeader, title } from './ui.js';

const STATE_LABEL = { stored: 'Guardado', out: 'Fora' };
const STEPS = ['Solicitado', 'Despachando', 'A caminho', 'Chegou'];
const STEP_MS = 1500;

const REAL_VEHICLE = { id: 'chiron', name: 'Bugatti Chiron' };
const RETRY_UI_MS = 1500; // the server enforces the real cooldown; this only stops accidental double clicks

/** The one REAL vehicle: asks the server (vehicles.call) to spawn the test car next to the player. */
function realVehicleRow(ctx) {
  const status = h('p', { class: 'footnote', role: 'status', 'data-testid': 'chiron-status' });
  const btn = h('button', { type: 'button', class: 'pill', 'data-testid': 'chiron-call', 'aria-label': 'Chamar veículo' }, 'Chamar');
  const routeSwitch = h('button', { type: 'button', class: 'switch', role: 'switch', 'aria-checked': 'false', 'aria-label': 'Traçar rota GPS', 'data-testid': 'route-switch' }, h('i'));
  const routeRow = h('div', { class: 'cell', 'data-testid': 'route-row', hidden: true },
    h('span', { class: 'glyph glyph-blue' }, icon('pix', 18)), h('span', { class: 'li-main' }, h('span', { class: 'li-title' }, 'Traçar rota GPS'), h('span', { class: 'li-sub' }, 'Até o veículo, no mapa')), routeSwitch);
  routeSwitch.addEventListener('click', async () => {
    const next = routeSwitch.getAttribute('aria-checked') !== 'true';
    const res = await post('phone:vehicleRoute', { on: next });
    if (res && res.ok) {
      routeSwitch.setAttribute('aria-checked', String(next));
    } else {
      routeRow.hidden = true; // the vehicle no longer exists on the map
      setStatus('err', 'O veículo não está mais disponível no mapa.');
    }
  });
  let pending = false;
  let timer = null;

  function setStatus(kind, text) {
    status.className = `footnote ${kind}`;
    status.textContent = text;
  }

  async function call() {
    if (pending) return; // one intent = one request; the server also refuses duplicates
    pending = true;
    btn.disabled = true;
    btn.textContent = '…';
    routeRow.hidden = true;
    setStatus('', 'Criando e verificando no jogo…');
    try {
      await ctx.request('vehicles.call', { vehicleId: REAL_VEHICLE.id });
      // reached only after the game confirmed it can see the vehicle (server waits for that)
      setStatus('ok', `${REAL_VEHICLE.name} confirmado no jogo e marcado no mapa. Entre e dirija!`);
      routeRow.hidden = false;
      routeSwitch.setAttribute('aria-checked', 'false');
    } catch (res) {
      setStatus('err', (res && res.error && res.error.message) || 'Não foi possível chamar o veículo.');
    } finally {
      timer = setTimeout(() => { pending = false; btn.disabled = false; btn.textContent = 'Chamar'; }, RETRY_UI_MS);
    }
  }
  btn.addEventListener('click', call);

  const row = h('div', { class: 'cell', 'data-testid': 'chiron-card' },
    h('span', { class: 'glyph glyph-orange' }, icon('car', 20)),
    h('span', { class: 'li-main' }, h('span', { class: 'li-title' }, REAL_VEHICLE.name), h('span', { class: 'li-sub' }, 'Aparece no jogo')),
    btn);
  return { el: h('div', { class: 'stack' }, group(row, routeRow), status), cleanup: () => { if (timer) clearTimeout(timer); } };
}

export function vehicleList(_param, ctx) {
  const items = vehicles.map((v) => listItem({ title: v.name, sub: v.plate, meta: STATE_LABEL[v.state],
    onclick: () => ctx.router.push(`veh.detail/${v.id}`) }));
  const real = realVehicleRow(ctx);
  return { el: h('section', { class: 'screen' }, title('Veículos'), sectionHeader('Veículo de teste'), real.el,
    sectionHeader('Demonstração'), items.length ? group(...items) : emptyState('Nenhum veículo.')), cleanup: real.cleanup };
}

export function vehicleDetail(id, ctx) {
  const v = vehicles.find((x) => x.id === id);
  if (!v) return { el: h('section', { class: 'screen' }, title('Veículo'), emptyState('Veículo não encontrado.')) };
  const callable = v.state === 'stored';
  return { el: h('section', { class: 'screen' }, title(v.name),
    group(h('div', { class: 'cell' }, h('span', { class: 'li-title' }, 'Placa'), h('span', { class: 'li-meta push' }, v.plate)),
      h('div', { class: 'cell' }, h('span', { class: 'li-title' }, 'Estado'), h('span', { class: 'li-meta push' }, STATE_LABEL[v.state]))),
    h('div', { class: 'list list-pad' }, meter('Combustível', v.fuel), meter('Motor', v.engine), meter('Lataria', v.body)),
    button('Chamar', () => ctx.router.push(`veh.call/${v.id}`), { disabled: !callable }),
    callable ? null : h('p', { class: 'footnote' }, 'Indisponível: veículo já está fora da garagem.')) };
}

/** Confirmation + status timeline. Purely visual: no server call, no vehicle is created. */
export function vehicleCall(id, ctx) {
  const v = vehicles.find((x) => x.id === id);
  if (!v || v.state !== 'stored') return { el: h('section', { class: 'screen' }, title('Chamar'), emptyState('Indisponível.')) };
  const body = h('section', { class: 'screen' });
  let step = -1;
  let timer = null;
  let confirmed = false;

  function renderConfirm() {
    body.replaceChildren(title('Confirmar'), h('p', { class: 'muted' }, `Chamar ${v.name} (${v.plate})? ETA fictícia: 15 s.`),
      banner('DEMONSTRAÇÃO — nenhum veículo é criado no jogo.'),
      button('Confirmar', onConfirm), button('Cancelar', () => ctx.router.back(), { kind: 'ghost' }));
  }

  function renderStatus() {
    const done = step >= STEPS.length - 1;
    body.replaceChildren(title('Status'), h('ol', { class: 'timeline', 'data-testid': 'timeline' },
      STEPS.map((s, i) => h('li', { class: i <= step ? 'on' : '' }, s))),
    banner('DEMONSTRAÇÃO — sem veículo real.'),
    button(done ? 'Voltar à garagem' : 'Cancelar chamada', () => ctx.router.home(), { kind: done ? 'primary' : 'ghost', settleMs: 500 }));
  }

  function onConfirm() {
    if (confirmed) return; // double click must not start a second call
    confirmed = true;
    step = 0;
    renderStatus();
    timer = setInterval(() => {
      step += 1;
      renderStatus();
      if (step >= STEPS.length - 1) { clearInterval(timer); timer = null; }
    }, STEP_MS);
  }

  renderConfirm();
  return { el: body, cleanup: () => { if (timer) clearInterval(timer); timer = null; } };
}
