import PropTypes from 'prop-types';

const LocalPropTypes = {
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

LocalPropTypes.options = PropTypes.arrayOf(PropTypes.object);

export default LocalPropTypes;
