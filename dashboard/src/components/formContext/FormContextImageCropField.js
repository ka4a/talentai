import React, { useContext } from 'react';

import { FormImageCropInput } from '@components';
import { FormContext } from '@contexts';

function FormContextFileField(props) {
  const { form, setValue, fieldErrors } = useContext(FormContext);
  return (
    <FormImageCropInput
      form={form}
      setValue={setValue}
      errors={fieldErrors}
      {...props}
    />
  );
}

export default FormContextFileField;
