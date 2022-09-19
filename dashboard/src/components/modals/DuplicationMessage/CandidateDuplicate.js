import React from 'react';
import { Link } from 'react-router-dom';

import PropTypes from 'prop-types';
import classnames from 'classnames';

function Candidate(props) {
  const { id, firstName, lastName, email, isAbsolute, linkedinUrl, onClick } = props;
  return (
    <div className='fs-12'>
      <Link
        target='__blank'
        onClick={onClick}
        to={`/candidate/${id}/edit`}
        className={classnames({ 'text-muted': !isAbsolute })}
      >
        {firstName} {lastName} {email} {linkedinUrl}{' '}
      </Link>
    </div>
  );
}

Candidate.propTypes = {
  onClick: PropTypes.func,
  id: PropTypes.number.isRequired,
  email: PropTypes.string,
  firstName: PropTypes.string,
  lastName: PropTypes.string,
  linkedinUrl: PropTypes.string,
  isAbsolute: PropTypes.bool,
};
Candidate.defaultProps = {
  onClick: null,
  email: '',
  firstName: '',
  lastName: '',
  linkedinUrl: '',
  isAbsolute: false,
};

export default Candidate;
