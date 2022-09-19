import React from 'react';

import PropTypes from 'prop-types';

export default class UserInline extends React.PureComponent {
  render() {
    const { photo, firstName, lastName } = this.props.user;

    return (
      <>
        {photo ? <img src={photo} className='avatar-small' alt='' /> : null}
        {firstName} {lastName}
      </>
    );
  }
}

UserInline.propTypes = {
  user: PropTypes.object.isRequired,
};
