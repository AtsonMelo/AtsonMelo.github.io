// Route stack. Routes are "name" or "name/param". No DOM here: unit-testable under node.
export function parseRoute(route) {
  const i = route.indexOf('/');
  return i < 0 ? { name: route, param: null } : { name: route.slice(0, i), param: route.slice(i + 1) };
}

export function createRouter(known, onChange) {
  const stack = ['home'];
  const isKnown = (route) => typeof route === 'string' && route.length <= 64 && known.includes(parseRoute(route).name);
  const emit = () => onChange(stack[stack.length - 1], stack.length);
  return {
    current: () => stack[stack.length - 1],
    depth: () => stack.length,
    canBack: () => stack.length > 1,
    previous: () => (stack.length > 1 ? stack[stack.length - 2] : null),
    isKnown,
    /** Unknown routes are ignored (deep links may come from the server). */
    push(route) {
      if (!isKnown(route) || route === stack[stack.length - 1]) return false;
      stack.push(route);
      emit();
      return true;
    },
    replace(route) {
      if (!isKnown(route)) return false;
      stack[stack.length - 1] = route;
      emit();
      return true;
    },
    back() {
      if (stack.length < 2) return false;
      stack.pop();
      emit();
      return true;
    },
    home() {
      if (stack.length === 1 && stack[0] === 'home') return false;
      stack.length = 1;
      stack[0] = 'home';
      emit();
      return true;
    },
  };
}
