import React from 'react';

import PropTypes from 'prop-types';
import moment from 'moment';

export default function UserActionDateInfo(props) {
  const { user, label, date } = props;

  return (
    <div className='d-flex justify-content-around'>
      <div className='font-weight-bold text-secondary'>{label}</div>
      <div>
        {!!user && <div>{[user.firstName, user.lastName].join(' ')}</div>}
        <div className='text-secondary font-weight-light fs-14'>
          {moment(date).format('llll')}
        </div>
      </div>
    </div>
  );
}

UserActionDateInfo.propTypes = {
  user: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
  }),
  label: PropTypes.node.isRequired,
  date: PropTypes.string.isRequired,
};
