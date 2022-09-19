import React, { memo } from 'react';
import { FaUserPlus } from 'react-icons/fa';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './Avatar.module.scss';

const Avatar = (props) => {
  const { src, size, shape, newUser, className, style, ...rest } = props;
  const classNames = classnames(styles[size], styles[shape], className);

  if (newUser) {
    return (
      <div
        className={classnames(classNames, styles.noImage)}
        style={{ backgroundColor: '#8593A3', ...style }}
        {...rest}
      >
        <FaUserPlus />
      </div>
    );
  }

  if (src) {
    return (
      <img src={src} className={classNames} alt='Account' style={style} {...rest} />
    );
  }

  return (
    <div
      className={classnames(classNames, styles.noImage)}
      style={{ ...style }}
      {...rest}
    />
  );
};

Avatar.propTypes = {
  src: PropTypes.string,
  size: PropTypes.oneOf(['sm', 'lg', 'xs']),
  shape: PropTypes.oneOf(['circle', 'square']),
  style: PropTypes.object,
  newUser: PropTypes.bool,
};

Avatar.defaultProps = {
  src: null,
  size: 'xs',
  shape: 'circle',
  style: {},
  newUser: false,
};

export default memo(Avatar);
