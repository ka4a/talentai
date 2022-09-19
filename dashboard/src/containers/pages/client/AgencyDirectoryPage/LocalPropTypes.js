import PropTypes from 'prop-types';

const LocalPropTypes = {
  option: PropTypes.shape({
    id: PropTypes.number,
    title: PropTypes.string,
  }),
  categoryGroups: PropTypes.arrayOf(PropTypes.string),
};
LocalPropTypes.arrayOfOptions = PropTypes.arrayOf(LocalPropTypes.option);

export default LocalPropTypes;
