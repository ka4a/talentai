import { createContext } from 'react';

const FormContext = createContext({
  form: {},
  initialForm: {},
  fieldErrors: {},
  setFieldErrors: (/* newFieldErrors */) => {},
  onValidate: (/* partialForm */) => {
    /* { fieldErrors: {} } */
  },
  changeForm: (/* formChanges */) => {},
  setValue: (/* path, value */) => {},
  setForm: (/* formReplacement */) => {},
  onSubmit: (/* form */) => {},
});

export default FormContext;
