import React, { useState, useMemo, useCallback } from 'react';

import { set } from 'lodash';
import PropTypes from 'prop-types';

import { FormContext } from '@contexts';

function FormContextProvider(props) {
  const { children, initialForm, onSubmit, onValidate } = props;

  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState(INITIAL_FIELD_ERRORS);

  const handleSubmit = useCallback(async () => {
    const report = await onSubmit(form);

    setFieldErrors(report?.fieldErrors ?? INITIAL_FIELD_ERRORS);

    if (report?.formUpdates) setForm((form) => ({ ...form, ...report.formUpdates }));

    return report;
  }, [onSubmit, form]);

  const handleValidate = useCallback(
    async (partialForm) => {
      const validationResult = await onValidate(partialForm);

      setFieldErrors((prevFieldErrors) => ({
        ...prevFieldErrors,
        ...validationResult,
      }));
    },
    [onValidate]
  );

  const setValue = useCallback(
    (name, value) =>
      setForm((prevForm) => {
        const newForm = { ...prevForm };
        set(newForm, name, value);
        return newForm;
      }),
    []
  );

  const resetForm = useCallback(() => {
    setForm(initialForm);
    setFieldErrors(INITIAL_FIELD_ERRORS);
  }, [initialForm]);

  const contextValue = useMemo(
    () => ({
      form,
      initialForm,
      fieldErrors,
      onSubmit: handleSubmit,
      setForm,
      resetForm,
      setValue,
      setFieldErrors,
      onValidate: handleValidate,
    }),
    [form, initialForm, fieldErrors, handleValidate, setValue, handleSubmit, resetForm]
  );

  return <FormContext.Provider value={contextValue}>{children}</FormContext.Provider>;
}

const INITIAL_FIELD_ERRORS = {};

FormContextProvider.propTypes = {
  onSubmit: PropTypes.func,
  onValidate: PropTypes.func,
  initialForm: PropTypes.object,
};

FormContextProvider.defaultProps = {
  onSubmit() {},
  onValidate() {},
  initialForm: {},
};

export default FormContextProvider;
