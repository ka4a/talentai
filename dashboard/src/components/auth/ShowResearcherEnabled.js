import { connect } from 'react-redux';

import PropTypes from 'prop-types';

const wrapper = connect((state) => ({
  user: state.user,
}));

const propTypes = {
  user: PropTypes.shape({
    isAuthenticated: PropTypes.bool.isRequired,
    isResearcher: PropTypes.bool.isRequired,
  }).isRequired,
  placeholder: PropTypes.node,
};

const defaultProps = {
  placeholder: null,
};

const ShowResearcherEnabled = ({ user, children, placeholder }) =>
  user.isAuthenticated && user.isResearcher ? children : placeholder;

ShowResearcherEnabled.propTypes = propTypes;
ShowResearcherEnabled.defaultProps = defaultProps;

export default wrapper(ShowResearcherEnabled);
