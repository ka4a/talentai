import React from 'react';
import { UncontrolledTooltip } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { Avatar, Typography } from '@components';

import styles from './NameAndAvatarCell.module.scss';

function NameAndAvatarCell({ tooltipId, name, avatarSrc }) {
  return (
    <div className={styles.root}>
      <Avatar shape='circle' src={avatarSrc} />

      <Typography
        id={tooltipId}
        variant='bodyStrong'
        className={classnames('user-name', styles.name)}
      >
        {name.length > 50 ? `${name.substr(0, 50)}...` : name}
      </Typography>

      <UncontrolledTooltip target={tooltipId}>{name}</UncontrolledTooltip>
    </div>
  );
}

NameAndAvatarCell.propTypes = {
  tooltipId: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  avatarSrc: PropTypes.string,
};

export default NameAndAvatarCell;
