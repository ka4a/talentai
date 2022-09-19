import { useRef, useEffect } from 'react';

export default function useFocusIfTrue(isTrue) {
  const ref = useRef();
  useEffect(() => {
    if (isTrue && ref.current) {
      const elem = ref.current;
      setTimeout(() => elem.focus(), 0);
    }
  }, [isTrue]);
  return ref;
}
