import React, { memo, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router';
import { Container } from 'reactstrap';
import { useHistory } from 'react-router-dom';

import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useJobsRead } from '@swrAPI';
import { openAddCandidateToJob } from '@actions';
import {
  useIsAllowedToOpenJobForm,
  useIsAuthenticatedByRoles,
  useTranslatedChoices,
} from '@hooks';
import { getChoiceName } from '@utils';
import {
  FormattedSalary,
  Badge,
  Tabs,
  Typography,
  Button,
  AddCandidateToJobModal,
  InfoTag,
} from '@components';
import {
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  CLIENT_STANDARD_USERS,
  JOB_STATUS_BADGE_COLORS,
  JOB_STATUS_CHOICES,
} from '@constants';

import Applications from '../Applications';
import JobOpenSince from './components/JobOpenSince';
import JobDetails from '../JobDetails';
import TabShareExternally from '../TabShareExternally';

import styles from './JobPageContent.module.scss';

const JobPageContent = () => {
  const { proposalId, tabId, jobId } = useParams();
  const history = useHistory();

  const handleChangeTab = useCallback(
    (newTabId) => {
      if (newTabId === TAB_IDS.details) newTabId = '';
      history.replace(getJobPath(jobId, newTabId));
    },
    [jobId, history]
  );

  let activeTabId = tabId;
  if (!activeTabId) activeTabId = proposalId ? TAB_IDS.applications : TAB_IDS.details;

  const { data: job, mutate: refreshJob } = useJobsRead();

  const { isAllowedToEdit, isAdmin, canViewAsStandardUser } = useUserRoles(job);

  const { i18n } = useLingui();
  const jobStatusChoices = useTranslatedChoices(i18n, JOB_STATUS_CHOICES);

  const badgeLabel = getChoiceName(jobStatusChoices, job.status);

  const tabs = useMemo(() => {
    const localTabs = [
      {
        id: TAB_IDS.details,
        title: t`Job Details`,
        component: <JobDetails job={job} refreshJob={refreshJob} />,
      },
    ];

    if (isAdmin || canViewAsStandardUser) {
      // TODO: refactor to pass job. Scope of refactoring would touch useProposalList
      localTabs.push({
        id: TAB_IDS.applications,
        title: t`Applications`,
        component: <Applications />,
      });
    }

    localTabs.push({
      id: TAB_IDS.share,
      title: t`Share Externally`,
      component: (
        <TabShareExternally job={job} refreshJob={refreshJob} isAdmin={isAdmin} />
      ),
    });

    return localTabs;
  }, [canViewAsStandardUser, isAdmin, job, refreshJob]);

  const dispatch = useDispatch();
  const openAddCandidateToJobModal = useCallback(() => {
    dispatch(openAddCandidateToJob());
  }, [dispatch]);

  return (
    <div className={styles.header}>
      <div className={styles.mainHeader}>
        <Container className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <Typography variant='h1' className={styles.title}>
              {job.title}
            </Typography>

            <Badge
              text={badgeLabel}
              variant={JOB_STATUS_BADGE_COLORS[job.status]}
              className={styles.badge}
            />

            <div className={styles.date}>
              <JobOpenSince job={job} />
            </div>
          </div>

          <div className={styles.headerRight}>
            {job.function && (
              <InfoTag className={styles.function}>{job.function.title}</InfoTag>
            )}

            {job.salaryTo && job.salaryFrom && (
              <InfoTag>
                <FormattedSalary job={job} hidePerName />
                <span className={styles.textLight}>&nbsp;{`/ ${job.salaryPer}`}</span>
              </InfoTag>
            )}
          </div>
        </Container>
      </div>

      <div className={styles.contentWrapper}>
        <Container className={styles.buttonsContainer}>
          <div className={styles.buttonWrapper}>
            {isAdmin && (
              <>
                <Button
                  variant='secondary'
                  to={getJobPath(jobId, 'edit')}
                  disabled={!isAllowedToEdit}
                  isLink
                >
                  <Trans>Edit</Trans>
                </Button>

                <Button onClick={openAddCandidateToJobModal}>
                  <Trans>Add Candidate to Job</Trans>
                </Button>

                <AddCandidateToJobModal listMode='candidates' />
              </>
            )}
          </div>
        </Container>

        <Tabs
          onChangeTab={handleChangeTab}
          className={styles.tabs}
          activeTabId={activeTabId}
          tabs={tabs}
        />
      </div>
    </div>
  );
};

const getJobPath = (jobId, suffix = '') => `/job/${jobId}/${suffix}`;

const useUserRoles = (job) => {
  const user = useSelector((state) => state.user);

  const isAllowedToEdit = useIsAllowedToOpenJobForm();

  const isStandardUser = useIsAuthenticatedByRoles([CLIENT_STANDARD_USERS]);
  const isAdmin = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);

  const isHiringManager = Boolean(job.managers?.find((el) => el.id === user.id));
  const isInterviewer = Boolean(
    job.interviewTemplates?.find((el) => el.interviewer?.id === user.id)
  );

  return {
    isAllowedToEdit,
    isAdmin,
    canViewAsStandardUser: isStandardUser && (isHiringManager || isInterviewer),
  };
};

const TAB_IDS = {
  share: 'share',
  applications: 'proposals',
  details: 'details',
};

export default memo(JobPageContent);
