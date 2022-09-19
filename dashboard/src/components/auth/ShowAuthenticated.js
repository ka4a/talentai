import PropTypes from 'prop-types';

import { useIsAuthenticatedByRoles } from '@hooks';

const ShowAuthenticated = ({ groups, children, placeholder }) => {
  const isAuthenticated = useIsAuthenticatedByRoles(groups);
  return isAuthenticated ? children : placeholder;
};

ShowAuthenticated.propTypes = {
  groups: PropTypes.arrayOf(PropTypes.string),
  placeholder: PropTypes.node,
};

ShowAuthenticated.defaultProps = {
  groups: null,
  placeholder: null,
};

export default ShowAuthenticated;
