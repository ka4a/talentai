import React from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import Avatar from '@components/UI/Avatar/Avatar';
import { Typography } from '@components';

import styles from './PersonDetailsHeader.module.scss';

function PersonDetailsHeader(props) {
  const { title, avatarSrc, controls, children, shouldControlsOverlapTabs } = props;

  return (
    <div className={styles.root}>
      <Avatar shape='circle' size='sm' src={avatarSrc} className={styles.avatar} />
      <div className={styles.content}>
        <Typography variant='h1' className={styles.title}>
          {title}
        </Typography>
        <div
          className={classNames(styles.controls, {
            [styles.overlapTab]: shouldControlsOverlapTabs,
          })}
        >
          {controls}
        </div>
        {children}
      </div>
    </div>
  );
}

PersonDetailsHeader.propTypes = {
  avatarSrc: PropTypes.string,
  title: PropTypes.string,
  controls: PropTypes.node,
  shouldControlsOverlapTabs: PropTypes.bool,
};

export default PersonDetailsHeader;
