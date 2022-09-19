import React, { memo } from 'react';
import { Container } from 'reactstrap';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

import { t, Trans } from '@lingui/macro';

import {
  Loading,
  Logo,
  DefaultPageContainer,
  Typography,
  WindowBackground,
} from '@components';
import { INTERVIEW_STATUSES } from '@constants';
import { useProposalInterviewPublicRead } from '@swrAPI';

import JobPostingHeader from '../JobPostingPageContent/components/JobPostingHeader/JobPostingHeader';
import ConfirmSchedule from './components/ConfirmSchedule';
import CandidateConfirmed from './components/CandidateConfirmed';
import RequestAdditionalTimeslots from './components/RequestAdditionalTimeslots';
import InterviewProposalCancelled from './components/InterviewProposalCancelled';

import styles from './CandidateConfirmation.module.scss';

const { scheduled, pending, rejected } = INTERVIEW_STATUSES;

const CandidateConfirmation = () => {
  const { publicUuid } = useParams();

  const { data: interview, loading, mutate } = useProposalInterviewPublicRead(
    publicUuid
  );
  const { job = {} } = interview;

  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);

  return (
    <DefaultPageContainer title={t`Candidate Confirmation`}>
      {!isAuthenticated && (
        <div className={styles.unauthenticatedHeader}>
          <Container>
            <Logo />
          </Container>
        </div>
      )}

      <JobPostingHeader job={job} />

      {loading ? (
        <Loading className={styles.loading} />
      ) : (
        <WindowBackground className={styles.wrapper}>
          <Typography variant='h3' className={styles.title}>
            <Trans>Confirm Interview Schedule</Trans>
          </Typography>

          {renderContent(interview, mutate)}
        </WindowBackground>
      )}
    </DefaultPageContainer>
  );
};

const renderContent = (interview, refreshInterview) => {
  const { preScheduleMsg, status } = interview;

  switch (status) {
    case pending:
      return (
        <ConfirmSchedule interview={interview} refreshInterview={refreshInterview} />
      );
    case scheduled:
      return <CandidateConfirmed interview={interview} />;
    case rejected:
      return <RequestAdditionalTimeslots />;
    default:
      break;
  }

  return <InterviewProposalCancelled message={preScheduleMsg} />;
};

export default memo(CandidateConfirmation);
