import React, { memo, useCallback } from 'react';
import { useDispatch } from 'react-redux';

import { Trans } from '@lingui/macro';

import { useProposalsRead } from '@swrAPI';
import { openInterviewEdit } from '@actions';
import { useIsAuthenticatedByRoles } from '@hooks';
import {
  Button,
  Typography,
  InterviewEditModal,
  InterviewSchedulingModal,
  InterviewAssessmentModal,
  CancelInterviewProposalModal,
} from '@components';
import { CLIENT_STANDARD_USERS } from '@constants';

import ProposalInterview from '../ProposalInterview';

import styles from './Sections.module.scss';

const ApplicationInterviews = () => {
  const { data, mutate } = useProposalsRead();
  const { interviews = [] } = data;

  const isStandardUser = useIsAuthenticatedByRoles([CLIENT_STANDARD_USERS]);

  const dispatch = useDispatch();

  const openAddInterviewModal = useCallback(() => {
    dispatch(openInterviewEdit());
  }, [dispatch]);

  return (
    <>
      <div className={styles.itemsSection}>
        <div className={styles.itemHeaderWrapper}>
          <Typography variant='subheading'>
            <Trans>Interviews</Trans>
          </Typography>

          {!isStandardUser && (
            <Button variant='secondary' onClick={openAddInterviewModal}>
              <Trans>Add Interview</Trans>
            </Button>
          )}
        </div>

        <div className={styles.itemsList}>
          {interviews.map((interview) => (
            <ProposalInterview key={interview.id} interview={interview} />
          ))}
        </div>
      </div>

      <InterviewEditModal />
      <InterviewSchedulingModal proposal={data} />
      <InterviewAssessmentModal />
      <CancelInterviewProposalModal onAfterSubmit={mutate} />
    </>
  );
};

export default memo(ApplicationInterviews);
