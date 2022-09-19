import React, { useCallback, useState } from 'react';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

import InputWithIcon from '../InputWithIcon';

export default function PasswordInput({ value, ...rest }) {
  const [isShowing, set] = useState(false);

  const toggle = useCallback(() => {
    set((state) => !state);
  }, [set]);

  const type = isShowing ? 'text' : 'password';
  const Icon = isShowing ? FaEyeSlash : FaEye;

  return (
    <InputWithIcon
      value={value}
      type={type}
      Icon={Icon}
      onIconClick={toggle}
      iconActive
      {...rest}
    />
  );
}
