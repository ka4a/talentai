import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import { Typography } from '@components';
import { ReactComponent as Clock } from '@images/icons/clockOutlined.svg';
import { formatSchedule } from '@utils';

import styles from './TimeslotDisplay.module.scss';

function TimeslotDisplay(props) {
  const { className } = props;
  const { startAt, endAt } = props.timeslot;

  return (
    <Typography className={classNames(styles.root, className)}>
      <Clock className={styles.clock} />
      {formatSchedule(startAt, endAt)}
    </Typography>
  );
}

TimeslotDisplay.propTypes = {
  className: PropTypes.string,
};

TimeslotDisplay.defaultProps = {
  className: '',
};

export default memo(TimeslotDisplay);
