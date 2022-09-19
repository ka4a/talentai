import React, { memo, useMemo } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import _ from 'lodash';

import BlockingPrompt from '@components/BlockingPrompt';

function BlockingPromptFormChanged({ initialForm, form, fieldsToSkip }) {
  // Set "has" check should be faster, than array "includes"
  // Think it's worth it, because we do this check to every field
  const fieldsToSkipSet = useMemo(() => (fieldsToSkip ? new Set(fieldsToSkip) : null), [
    fieldsToSkip,
  ]);

  let fieldsToCheck = _.keys(form);

  if (fieldsToSkipSet)
    fieldsToCheck = fieldsToCheck.filter((field) => !fieldsToSkipSet.has(field));

  const hasFormChanged = fieldsToCheck.some(
    (field) => !_.isEqual(form[field], initialForm[field])
  );

  return (
    <BlockingPrompt
      when={hasFormChanged}
      message={t`Some data is not saved. Are you sure you want to leave the page?`}
    />
  );
}

BlockingPromptFormChanged.propTypes = {
  initialForm: PropTypes.object.isRequired,
  form: PropTypes.object.isRequired,
  fieldsToSkip: PropTypes.arrayOf(PropTypes.string),
};

BlockingPromptFormChanged.defaultProps = {
  fieldsToSkip: null,
};

export default memo(BlockingPromptFormChanged);
