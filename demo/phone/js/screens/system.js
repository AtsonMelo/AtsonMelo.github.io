// States shown instead of the app screens when the channel to Lua is not usable (docs/phone/02 §7).
import { h } from '../dom.js';
import { button, title } from './ui.js';

const TEXT = {
  connecting: ['Conectando…', 'Aguardando o servidor.'],
  failed: ['Indisponível', 'Não foi possível falar com o servidor.'],
  protocol: ['Versão incompatível', 'Recarregue o recurso devlab_phone.'],
  error: ['Erro na interface', 'Algo falhou ao exibir esta tela.'],
};

export function systemScreen(kind, onRetry) {
  const [head, body] = TEXT[kind] || TEXT.error;
  return h('section', { class: 'screen system', 'data-state': kind }, title(head), h('p', { class: 'muted', role: 'status' }, body),
    onRetry && (kind === 'failed' || kind === 'error') ? button('Tentar novamente', onRetry, { kind: 'secondary' }) : null);
}
