/* Browser-only stand-in for FiveM + the Lua server, so the real phone NUI runs without a game.
   Loaded as a classic script BEFORE the NUI module. Everything is local and fictitious:
   it answers the NUI callbacks (https://devlab_phone/<name>) in-page and never touches the network. */
(function () {
  'use strict';
  var RES = 'devlab_phone';
  var realFetch = window.fetch.bind(window);
  window.GetParentResourceName = function () { return RES; };

  function toNui(action, data) { window.postMessage({ v: 1, action: action, data: data || {} }, '*'); }
  function clock() { var d = new Date(); toNui('clock', { hh: d.getHours(), mm: d.getMinutes() }); }
  function init(mode) {
    toNui('init', {
      protocol: 1,
      config: { hud: { offset: { right: 24, bottom: 24 }, safeZone: 1 } },
      snapshot: {
        player: { id: 1, verified: true },
        device: { model: 'DevLab One (demo)', battery: 82, signal: 5 },
        notifications: [
          { title: 'Banco', body: 'Pagamento simulado recebido', route: 'bank.home' },
          { title: 'Marina', body: 'Notificação demonstrativa', route: 'msg.list' }
        ]
      },
      mode: mode || 'PHONE'
    });
    clock();
  }
  setInterval(clock, 20000);

  var routes = {
    'ready': function () { setTimeout(function () { init('PHONE'); }, 30); return { ok: true }; },
    'phone:retryInit': function () { setTimeout(function () { init('PHONE'); }, 30); return { ok: true }; },
    'phone:close': function () { setTimeout(function () { toNui('mode', { mode: 'CURSOR' }); }, 0); return { ok: true }; },
    'phone:openFromButton': function () { setTimeout(function () { toNui('mode', { mode: 'PHONE' }); }, 0); return { ok: true }; },
    // The only server round-trip in the app: "call my vehicle". Simulated success after a short delay.
    'rpc': function (body) {
      setTimeout(function () {
        toNui('rpc:result', { requestId: body.requestId, ok: true, data: { vehicleId: (body.args || {}).vehicleId, status: 'arrived', netId: 0 } });
      }, 1400);
      return { ok: true, accepted: true };
    }
  };

  window.fetch = function (url, opts) {
    var u = String(url);
    var prefix = 'https://' + RES + '/';
    if (u.indexOf(prefix) !== 0) return realFetch(url, opts);
    var name = u.slice(prefix.length);
    var body = {};
    try { body = JSON.parse((opts && opts.body) || '{}'); } catch (e) { /* ignore */ }
    var res = routes[name] ? routes[name](body) : { ok: true };
    return Promise.resolve({ json: function () { return Promise.resolve(res); } });
  };
})();
