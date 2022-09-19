import { connect } from 'react-redux';

const mapStateToProps = (state) => ({
  user: state.user,
});

const ShowAnonymous = ({ user, children }) => (!user.isAuthenticated ? children : null);

export default connect(mapStateToProps)(ShowAnonymous);
