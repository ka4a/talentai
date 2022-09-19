import React, { memo, useMemo } from 'react';

import { Trans } from '@lingui/macro';
import flatten from 'lodash/flatten';

import { useProposalsRead } from '@swrAPI';
import { formatTimeslot } from '@utils';
import { Badge, Typography } from '@components';

import styles from '../InterviewSchedulingModal.module.scss';

const RejectedTimeslots = () => {
  const { data } = useProposalsRead();
  const { schedules } = data.currentInterview;

  const rejectedTimeslots = useMemo(
    () => flatten(schedules.map((schedule) => schedule.timeslots)),
    [schedules]
  );

  if (rejectedTimeslots.length === 0) return null;

  return (
    <>
      <Typography>
        <Trans>Time slots previously Declined or Cancelled:</Trans>
      </Typography>

      <div className={styles.badges}>
        {rejectedTimeslots.map(({ id, startAt, endAt }) => {
          const timeRange = formatTimeslot(startAt, endAt);
          return timeRange && <Badge key={id} text={timeRange} variant='danger' />;
        })}
      </div>
    </>
  );
};

export default memo(RejectedTimeslots);
