import React, { memo } from 'react';
import { Link } from 'react-router-dom';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from '@styles/button.module.scss';

import Typography from '../Typography';

const Button = (props) => {
  const {
    variant,
    color,
    disabled,
    onClick,
    isLink,
    to,
    className: wrapperClassname,
    children,
    id,
  } = props;

  const button = <Typography variant='button'>{children}</Typography>;
  const className = classnames([styles.button, styles[variant], styles[color]]);

  return (
    <div className={wrapperClassname}>
      {isLink && !disabled ? (
        <Link id={id} className={className} to={to}>
          {button}
        </Link>
      ) : (
        <button
          id={id}
          type='button'
          onClick={onClick}
          disabled={disabled}
          className={className}
        >
          {button}
        </button>
      )}
    </div>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'text', 'dot']),
  color: PropTypes.oneOf(['success', 'danger', 'neutral', 'inverse', '']),
  disabled: PropTypes.bool,
  onClick: PropTypes.func,
  isLink: PropTypes.bool,
  to: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  className: PropTypes.string,
  id: PropTypes.string,
};

Button.defaultProps = {
  variant: 'primary',
  color: '',
  disabled: false,
  onClick: () => {},
  isLink: false,
  to: '',
  className: '',
};

export default memo(Button);
