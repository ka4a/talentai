import React, { memo } from 'react';

import moment from 'moment';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import { DATE_FORMAT } from '@constants';
import { Button, TableRow, Typography } from '@components';

import styles from '../CandidateConfirmation.module.scss';

const Timeslot = (props) => {
  const { isActive, onRowClick, onSelect } = props;

  const startAt = moment(props.startAt);
  const endAt = moment(props.endAt);

  return (
    <TableRow className={styles.timeslot} isActive={isActive} onClick={onRowClick}>
      <div className={styles.dateTime}>
        <Typography variant='bodyStrong' className={styles.date}>
          {startAt.format(DATE_FORMAT.moment)} ({startAt.format('ddd')})
        </Typography>

        <Typography
          variant='bodyStrong'
          className={classnames([styles.time, { [styles.active]: isActive }])}
        >
          {startAt.format('HH:mm')}
          {' - '}
          {endAt.format('HH:mm')}
        </Typography>
      </div>

      {isActive && (
        <Button onClick={onSelect} variant='secondary' color='inverse'>
          <Trans>Confirm Schedule</Trans>
        </Button>
      )}
    </TableRow>
  );
};

Timeslot.propTypes = {
  isActive: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
  onRowClick: PropTypes.func.isRequired,
  startAt: PropTypes.string.isRequired,
  endAt: PropTypes.string.isRequired,
};

export default memo(Timeslot);
