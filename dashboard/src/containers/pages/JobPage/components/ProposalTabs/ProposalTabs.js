import React, { memo, useCallback, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useLocation } from 'react-router-dom';

import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import {
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  PROPOSAL_STAGES,
} from '@constants';
import { useGetJob, useProposalsList, useProposalsRead } from '@swrAPI';
import { useIsAuthenticatedByRoles } from '@hooks';
import { fetchErrorHandler } from '@utils';
import { client } from '@client';
import {
  openInterviewScheduling,
  openRejection,
  openInterviewAssessment,
} from '@actions';
import {
  Button,
  QuickActionButton,
  Tabs,
  CandidateDetailsTab,
  RejectionModal,
} from '@components';

import ApplicationTab from '../ProposalApplication/ProposalApplication';

import styles from './ProposalTabs.module.scss';

const ProposalTabs = () => {
  const [activeProposalTab, setActiveProposalTab] = useState(1);
  const { i18n } = useLingui();

  const user = useSelector((state) => state.user);
  const { data: proposal } = useProposalsRead();
  const { candidate, quickActions, own, isRejected, stage, job } = proposal;

  const { pathname: localPathname } = useLocation();

  const {
    areQuickActionsShown,
    onQuickAction,
    reactivateCandidate,
  } = useGetQuickActions(activeProposalTab);

  const isAdmin = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);
  const isHiringManager = Boolean(job.managers?.find((el) => el.id === user.id));

  const isApplicationTab = activeProposalTab === 1;
  const shouldShowEditButton =
    isAdmin && own && !candidate?.archived && activeProposalTab === 2;
  const shouldShowQuickActionButtons =
    areQuickActionsShown &&
    (isAdmin || (isHiringManager && stage === PROPOSAL_STAGES.submissions));

  const tabs = useMemo(
    () => [
      {
        id: 1,
        title: t`Application`,
        component: <ApplicationTab />,
      },
      {
        id: 2,
        title: t`Candidate Details`,
        component: <CandidateDetailsTab />,
      },
    ],
    // Wee need i18n here to update translation as locale updates
    [i18n] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <>
      <div className={styles.actionsWrapper}>
        {shouldShowEditButton && (
          <Button
            className={styles.editButton}
            variant='secondary'
            to={{
              pathname: `/candidate/${candidate.id}/edit`,
              returningPath: localPathname,
            }}
            isLink
          >
            <Trans>Edit</Trans>
          </Button>
        )}

        {shouldShowQuickActionButtons && (
          <div className={styles.quickActionsWrapper}>
            {quickActions.map((action) => (
              <QuickActionButton
                key={action.action}
                action={action}
                onClick={onQuickAction}
              />
            ))}
          </div>
        )}

        {isRejected && isAdmin && isApplicationTab && (
          <Button
            className={styles.quickActionsWrapper}
            variant='secondary'
            onClick={reactivateCandidate}
          >
            <Trans>Reactivate Candidate</Trans>
          </Button>
        )}
      </div>

      <RejectionModal />

      <Tabs
        activeTabId={activeProposalTab}
        onChangeTab={setActiveProposalTab}
        tabs={tabs}
      />
    </>
  );
};

const useGetQuickActions = (activeProposalTab) => {
  const { mutate: refreshJob } = useGetJob();
  const { mutate: refreshStages } = useProposalsList();

  const { data: proposal, mutate: refreshProposal } = useProposalsRead();
  const { quickActions, isRejected, currentInterview } = proposal;

  const refreshData = useCallback(async () => {
    await Promise.all([refreshJob(), refreshProposal(), refreshStages()]);
  }, [refreshJob, refreshProposal, refreshStages]);

  const dispatch = useDispatch();
  const currentInterviewId = currentInterview?.id;

  const onQuickAction = useCallback(
    async ({ action, toStatus }) => {
      try {
        if (action === 'schedule') {
          if (currentInterviewId) dispatch(openInterviewScheduling(currentInterviewId));
          return;
        }

        if (action === 'assess') {
          if (currentInterviewId) dispatch(openInterviewAssessment(currentInterviewId));
          return;
        }

        if (action === 'reject') {
          dispatch(openRejection());
          return;
        }

        await client.execute({
          operationId: 'proposal_quick_actions',
          parameters: {
            id: proposal.id,
            data: { action, toStatus },
          },
        });
        await refreshData();
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [currentInterviewId, dispatch, proposal.id, refreshData]
  );

  const reactivateCandidate = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'proposals_partial_update',
        parameters: {
          id: proposal.id,
          data: { isRejected: false },
        },
      });
      await refreshData();
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [proposal.id, refreshData]);

  const areQuickActionsShown =
    quickActions?.length > 0 && activeProposalTab === 1 && !isRejected;

  return {
    areQuickActionsShown,
    onQuickAction,
    reactivateCandidate,
  };
};

export default memo(ProposalTabs);
