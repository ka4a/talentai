import React, { memo, useContext, useMemo } from 'react';

import PropTypes from 'prop-types';

import { FormContext } from '@contexts';
import { DynamicList, FormContextField } from '@components';
import {
  useAddDynamicListRow,
  useRemoveDynamicListRow,
} from '@components/formContext/hooks';

function FormContextLanguageField(props) {
  const { name, fields, rowTemplate, ...rest } = props;

  const { form, setForm } = useContext(FormContext);

  const addRow = useAddDynamicListRow(setForm, name, rowTemplate);
  const removeRow = useRemoveDynamicListRow(setForm, name);

  const defaultFields = useMemo(
    () => [
      {
        id: 1,
        render: (index) => (
          <FormContextField label={String(index + 1)} name={`${name}[${index}].text`} />
        ),
      },
    ],
    [name]
  );

  return (
    <DynamicList
      {...rest}
      fields={fields ?? defaultFields}
      data={form[name]}
      onAddRow={addRow}
      onRemoveRow={removeRow}
      FormInput={FormContextField}
    />
  );
}

FormContextLanguageField.propTypes = {
  name: PropTypes.string.isRequired,
  fields: PropTypes.oneOfType([
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number,
        render: PropTypes.func,
      })
    ),
    PropTypes.func,
  ]),
  rowTemplate: PropTypes.object,
};

export default memo(FormContextLanguageField);
