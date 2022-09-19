import { memo } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';

const LocaleOptionsProvider = ({ render, optionsKey }) => {
  const options = useSelector((state) => state.settings.localeData[optionsKey]);
  return render(options);
};

LocaleOptionsProvider.propTypes = {
  optionsKey: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ),
};

LocaleOptionsProvider.defaultProps = {
  options: [],
};

export default memo(LocaleOptionsProvider);
