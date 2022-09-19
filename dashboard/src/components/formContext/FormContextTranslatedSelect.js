import React, { memo } from 'react';

import { useLingui } from '@lingui/react';
import PropTypes from 'prop-types';

import { FormContextField } from '@components';
import { useTranslatedChoices } from '@hooks';

function FormContextTranslatedSelect(props) {
  const { options, ...rest } = props;

  const { i18n } = useLingui();
  const translatedOptions = useTranslatedChoices(i18n, options);

  return <FormContextField options={translatedOptions} {...rest} />;
}

FormContextTranslatedSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
    })
  ).isRequired,
  type: PropTypes.string,
};

FormContextTranslatedSelect.defaultProps = {
  type: 'select',
};

export default memo(FormContextTranslatedSelect);
