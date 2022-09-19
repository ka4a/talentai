import { useState, useRef, useCallback, useMemo } from 'react';
import { keyCodes } from 'reactstrap/es/utils';

const invert = (value) => !value;

export default function useToggleState(defaultState = false) {
  const [value, set] = useState(defaultState);
  const containerRef = useRef();

  const toggle = useCallback((e) => {
    const container = containerRef.current;
    /*
      Dropdowns considers clicks on elements, what aren't children
      to be clicks outside and closes itself.
      Since menu isn't child, it closes then you click on it
      (even before option is picked)
      To prevent that we check if click was inside the portal before we toggle state
    */
    if (
      container &&
      container.contains(e.target) &&
      container !== e.target &&
      // Also there is a key check to not break original logic with keypresses
      (e.type !== 'keyup' || e.which === keyCodes.tab)
    ) {
      return;
    }

    set(invert);
  }, []);

  return useMemo(
    () => ({
      set,
      value,
      containerRef,
      toggle,
    }),
    [value, toggle]
  );
}
