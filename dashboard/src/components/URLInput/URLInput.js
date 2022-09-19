import React from 'react';
import { FaExternalLinkAlt } from 'react-icons/fa';

import InputWithIcon from '../InputWithIcon';

const isValidURL = (str) => {
  const pattern = new RegExp(
    '^(https?:\\/\\/)' + // protocol
      '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
      '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
      '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
      '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
      '(\\#[-a-z\\d_]*)?$',
    'i'
  ); // fragment locator
  return !!pattern.test(str);
};

export default function URLInput({ value, ...rest }) {
  const isValid = isValidURL(value);
  const onIconClick = isValid ? () => window.open(value, '_blank') : null;

  return (
    <InputWithIcon
      value={value}
      Icon={isValid ? FaExternalLinkAlt : null}
      iconActive
      onIconClick={onIconClick}
      {...rest}
    />
  );
}
