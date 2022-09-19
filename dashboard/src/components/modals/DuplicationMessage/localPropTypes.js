import PropTypes from 'prop-types';

const LocalPropTypes = {};
LocalPropTypes.candidate = PropTypes.shape({
  id: PropTypes.number,
  isAbsolute: PropTypes.bool,
  isSubmitted: PropTypes.bool,
  firstName: PropTypes.string,
  lastName: PropTypes.string,
  linkedinUrl: PropTypes.string,
});

export default LocalPropTypes;
