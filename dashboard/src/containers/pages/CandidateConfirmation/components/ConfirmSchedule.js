import React, { memo, useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';

import { Trans } from '@lingui/macro';

import { client } from '@client';
import { handleRequestError } from '@utils';
import { Button, TimezoneDisplay, Typography } from '@components';

import Timeslot from './Timeslot';

import styles from '../CandidateConfirmation.module.scss';

const ConfirmSchedule = ({ interview, refreshInterview }) => {
  const [activeTimeslot, setActiveTimeslot] = useState();

  const { publicUuid } = useParams();

  const { inviter, timeslots, candidateName } = interview;

  const onRowClick = useCallback((id) => {
    setActiveTimeslot(id);
  }, []);

  const onSelect = useCallback(
    async (chosenTimeslot, isRejected = false) => {
      const data = { isRejected };

      if (chosenTimeslot) {
        data.chosenTimeslot = chosenTimeslot;
      }

      try {
        await client.execute({
          operationId: 'proposal_interviews_public_partial_update',
          parameters: { public_uuid: publicUuid, data },
        });

        await refreshInterview();
      } catch (e) {
        handleRequestError(e, 'patch');
      }
    },
    [refreshInterview, publicUuid]
  );

  const requestAdditionalTimeslots = useCallback(() => onSelect(null, true), [
    onSelect,
  ]);

  return (
    <>
      <Typography className={styles.greeting}>
        <Trans>
          Hi <Typography variant='bodyStrong'>{candidateName}</Typography>, you have
          been invited to an interview with
        </Trans>{' '}
        <Typography variant='bodyStrong'>{inviter}</Typography>.{' '}
        <Trans>Select a time slot for your interview.</Trans>
      </Typography>

      <TimezoneDisplay />

      {timeslots
        .filter((el) => !el.isRejected)
        .map((timeslot) => (
          <Timeslot
            key={timeslot.id}
            isActive={timeslot.id === activeTimeslot}
            onSelect={() => onSelect(timeslot.id)}
            onRowClick={() => onRowClick(timeslot.id)}
            startAt={timeslot.startAt}
            endAt={timeslot.endAt}
          />
        ))}

      <hr className={styles.divider} />

      <div className={styles.footer}>
        <Typography>
          <Trans>None of the time slots fit your schedule?</Trans>
        </Typography>

        <Button
          variant='secondary'
          color='neutral'
          onClick={requestAdditionalTimeslots}
        >
          <Trans>Request Additional Timeslots</Trans>
        </Button>
      </div>
    </>
  );
};

export default memo(ConfirmSchedule);
