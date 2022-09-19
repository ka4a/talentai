import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '@components/UI/Typography';

import styles from './InfoTag.module.scss';

const InfoTag = ({ children, className }) => (
  <Typography variant='caption' className={classnames([styles.wrapper, className])}>
    {children}
  </Typography>
);

InfoTag.propTypes = {
  children: PropTypes.node,
  className: PropTypes.string,
};

InfoTag.defaultProps = {
  children: null,
  className: '',
};

export default memo(InfoTag);
