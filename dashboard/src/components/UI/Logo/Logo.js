import React, { memo, useCallback } from 'react';
import { useHistory } from 'react-router-dom';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../Typography';

import styles from './Logo.module.scss';

const Logo = ({ variant, className }) => {
  const history = useHistory();

  const goHome = useCallback(() => {
    history.push('/');
  }, [history]);

  return (
    <Typography
      className={classnames([styles.logo, className])}
      onClick={goHome}
      variant={variant}
    >
      <span>Zoo</span>
      Keep
    </Typography>
  );
};

Logo.propTypes = {
  onClick: PropTypes.func,
  className: PropTypes.string,
  variant: PropTypes.string,
};

Logo.defaultProps = {
  onClick: null,
  variant: 'h1',
  className: '',
};

export default memo(Logo);
