import React, { memo } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Badge, LabeledItem } from '@components';
import { INTERVIEW_STATUSES } from '@constants';
import { formatTimeslot } from '@utils';

import Assessments from './Assessments';

import styles from '../ProposalInterview.module.scss';

const InterviewFullBody = ({ interview, interviewerName }) => {
  const { startAt, endAt, description, assessment, status, timeslots } = interview;

  return (
    <>
      <div className={styles.details}>
        {status === INTERVIEW_STATUSES.pending && (
          <LabeledItem
            label={t`Proposed time slots`}
            className={styles.timeslotsWrapper}
            value={
              <div className={styles.timeslotsBadges}>
                {timeslots
                  .filter((el) => !el.isRejected)
                  .map((el) => (
                    <Badge
                      key={el.id}
                      text={formatTimeslot(el.startAt, el.endAt)}
                      variant='neutral'
                    />
                  ))}
              </div>
            }
          />
        )}

        <div className={styles.interviewerWrapper}>
          <LabeledItem label={t`Interviewer`} value={interviewerName} />

          <LabeledItem
            label={t`Date and Time`}
            value={formatTimeslot(startAt, endAt)}
          />
        </div>

        <LabeledItem
          label={t`Interview Details`}
          variant='textarea'
          value={description}
        />
      </div>

      <Assessments data={assessment} />
    </>
  );
};

InterviewFullBody.propTypes = {
  interview: PropTypes.shape({}).isRequired,
  interviewerName: PropTypes.string.isRequired,
};

export default memo(InterviewFullBody);
