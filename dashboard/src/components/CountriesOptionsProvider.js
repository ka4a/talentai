import { memo, cloneElement } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';

const propTypes = {
  children: PropTypes.node,
};

const CountriesOptionsProvider = ({ children }) => {
  const options = useSelector((state) => state.settings.localeData.countries);
  return cloneElement(children, { options, getValue: (option) => option.code });
};

CountriesOptionsProvider.propTypes = propTypes;

export default memo(CountriesOptionsProvider);
