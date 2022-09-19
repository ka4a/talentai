import { useState } from 'react';

export default function useForceUpdate() {
  const setState = useState()[1];

  return () => setState({});
}
