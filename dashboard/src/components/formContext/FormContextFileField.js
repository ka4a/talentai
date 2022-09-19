import React, { useContext } from 'react';

import { FileInput } from '@components';
import { FormContext } from '@contexts';

function FormContextFileField(props) {
  const { form, setValue } = useContext(FormContext);
  return <FileInput form={form} setValue={setValue} {...props} />;
}

export default FormContextFileField;
