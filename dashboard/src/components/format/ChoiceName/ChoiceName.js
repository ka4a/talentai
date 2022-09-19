import { memo, useMemo } from 'react';

import PropTypes from 'prop-types';

import { getChoiceName } from '@utils';

function ChoiceName(props) {
  const {
    nameField,
    choices,
    value,
    otherChoiceName,
    otherChoiceValue,
    formatOtherChoice,
  } = props;

  const choiceName = useMemo(() => getChoiceName(choices, value, nameField) || '', [
    choices,
    value,
    nameField,
  ]);
  const isOtherChoice =
    otherChoiceName !== undefined &&
    otherChoiceValue !== undefined &&
    otherChoiceValue === value;
  if (isOtherChoice) {
    if (formatOtherChoice) {
      return formatOtherChoice(otherChoiceName, choiceName);
    }
    return otherChoiceName;
  }
  return choiceName;
}

ChoiceName.propTypes = {
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.any,
      name: PropTypes.string,
    })
  ).isRequired,
  value: PropTypes.any.isRequired,
  otherChoiceValue: PropTypes.any,
  otherChoiceName: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  nameField: PropTypes.string,
  formatOtherChoice: PropTypes.func,
};

ChoiceName.defaultProps = {
  nameField: 'name',
};

export default memo(ChoiceName);
