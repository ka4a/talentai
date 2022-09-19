import React, { memo, useContext, useCallback } from 'react';

import PropTypes from 'prop-types';

import { FormContext } from '@contexts';
import { TagsInput } from '@components';

function FormContextTagsField(props) {
  const { name, ...rest } = props;

  const { form, setValue } = useContext(FormContext);

  const handleSave = useCallback(
    (value) => {
      setValue(name, value);
    },
    [setValue, name]
  );

  return <TagsInput {...rest} tags={form[name]} tagType='skill' onSave={handleSave} />;
}

FormContextTagsField.propTypes = {
  name: PropTypes.string.isRequired,
};

export default memo(FormContextTagsField);
