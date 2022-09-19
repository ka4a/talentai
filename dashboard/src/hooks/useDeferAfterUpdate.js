import { useLayoutEffect, useRef } from 'react';

export default function useDeferAfterUpdate() {
  const defered = useRef(null);
  useLayoutEffect(() => {
    if (defered.current) {
      defered.current();
      defered.current = null;
    }
  });
  return (deferedCallback) => {
    defered.current = deferedCallback;
  };
}
