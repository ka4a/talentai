import React, { memo, useContext, useCallback } from 'react';

import { get, set } from 'lodash';
import PropTypes from 'prop-types';

import { FormContext } from '@contexts';
import { getErrorsInputFeedback, getErrorsInputInvalid } from '@utils';
import CustomFormInput from '@components/SwaggerForm/CustomFormInput';

function FormContextField(props) {
  const { name, fieldWrapperClassName, ...rest } = props;

  const { form, setValue, setFieldErrors, fieldErrors, onValidate } = useContext(
    FormContext
  );

  const isInvalid = getErrorsInputInvalid(fieldErrors, name);

  const handleChange = useCallback(
    (event) => {
      setValue(name, event.target.value);

      if (isInvalid)
        setFieldErrors((oldFieldErrors) => {
          const newFieldErrors = { ...oldFieldErrors };
          // State mutation will occur here, if name is some nested reference
          // But it's probably fine, as update is still triggered
          // And the fields only care about values retrieved by name, which did change
          set(newFieldErrors, name, null);
        });
    },
    [setValue, name, isInvalid, setFieldErrors]
  );

  const value = get(form, name);

  const validate = useCallback(() => {
    const toValidate = {};
    // Form fields can reference nested form values. Set method accounts for that
    set(toValidate, name, value);

    onValidate(toValidate);
  }, [value, name, onValidate]);

  return (
    <div className={`d-flex flex-column ${fieldWrapperClassName}`}>
      <CustomFormInput
        name={name}
        onChange={handleChange}
        value={value}
        validate={validate}
        invalid={isInvalid}
        {...rest}
      />
      {getErrorsInputFeedback(fieldErrors, name)}
    </div>
  );
}

FormContextField.propTypes = {
  name: PropTypes.string.isRequired,
  fieldWrapperClassName: PropTypes.string,
};

FormContextField.defaultProps = {
  fieldWrapperClassName: '',
};

export default memo(FormContextField);
