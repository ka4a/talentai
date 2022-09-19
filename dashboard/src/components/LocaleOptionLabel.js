import { memo, useMemo } from 'react';
import { connect } from 'react-redux';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { compose } from 'redux';

const wrapper = compose(
  connect((state, props) => ({
    options: _.get(state.settings.localeData, props.optionsKey),
  })),
  memo
);

const LocaleOptionLabel = (props) => {
  const { value, placeholder, processOptions } = props;
  let { options } = props;

  options = useMemo(() => (processOptions ? processOptions(options) : options), [
    options,
    processOptions,
  ]);

  const option = useMemo(() => _.find(options, { value }), [options, value]);

  return option ? option.label : placeholder;
};

LocaleOptionLabel.propTypes = {
  value: PropTypes.string.isRequired,
  optionsKey: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  processOptions: PropTypes.func,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ),
};

LocaleOptionLabel.defaultProps = {
  options: [],
  placeholder: '',
};

export default wrapper(LocaleOptionLabel);
