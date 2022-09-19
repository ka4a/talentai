import React, { memo, useContext } from 'react';

import PropTypes from 'prop-types';

import { FormContext } from '@contexts';
import { FormContextField, LanguageInput } from '@components';
import {
  useAddDynamicListRow,
  useRemoveDynamicListRow,
} from '@components/formContext/hooks';

function FormContextLanguageField(props) {
  const { name, ...rest } = props;

  const { form, setForm } = useContext(FormContext);

  const addRow = useAddDynamicListRow(setForm, name, LANGUAGE_ROW_TEMPLATE);
  const removeRow = useRemoveDynamicListRow(setForm, name);

  return (
    <LanguageInput
      {...rest}
      inputName={name}
      languages={form[name]}
      addFieldRow={addRow}
      removeFieldRow={removeRow}
      FormInput={FormContextField}
    />
  );
}

const LANGUAGE_ROW_TEMPLATE = { language: null, level: null };

FormContextLanguageField.propTypes = {
  name: PropTypes.string.isRequired,
};

export default memo(FormContextLanguageField);
