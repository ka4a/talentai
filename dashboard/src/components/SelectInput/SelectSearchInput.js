import { Input } from 'reactstrap';
import React from 'react';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

function SelectSearchInput(props) {
  const { value, setValue, onKeyDown, disabled, i18n, innerRef } = props;
  return (
    <Input
      innerRef={innerRef}
      value={value}
      onChange={(event) => {
        setValue(event.target.value);
      }}
      placeholder={i18n._(t`Search...`)}
      onKeyDown={onKeyDown}
      disabled={disabled}
    />
  );
}

export default withI18n()(SelectSearchInput);
