import React from 'react';

import PropTypes from 'prop-types';

import LabeledItem from '@components/UI/LabeledItem';
import ChoiceName from '@components/format/ChoiceName';

function LabeledChoiceName({ label, ...choiceNameProps }) {
  return <LabeledItem label={label} value={<ChoiceName {...choiceNameProps} />} />;
}

LabeledChoiceName.propTypes = {
  ...ChoiceName.propTypes,
  label: PropTypes.string,
};

export default LabeledChoiceName;
