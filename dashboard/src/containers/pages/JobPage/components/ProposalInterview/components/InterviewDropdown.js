import React, { memo, useCallback } from 'react';
import { useDispatch } from 'react-redux';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import {
  openCancelInterviewProposal,
  openInterviewAssessment,
  openInterviewEdit,
} from '@actions';
import { INTERVIEW_STATUSES } from '@constants';
import { useProposalsList, useProposalsRead, updateInterview } from '@swrAPI';
import { fetchErrorHandler, isDialogCanceled } from '@utils';
import { ActionsDropdown } from '@components';
import { client } from '@client';

import {
  openCancelInterview,
  openDeleteInterview,
  openSkipInterview,
} from '../dialogs';

import styles from '../ProposalInterview.module.scss';

const {
  rejected,
  toBeScheduled,
  canceled,
  scheduled,
  skipped,
  pending,
} = INTERVIEW_STATUSES;
const TO_BE_SCHEDULED_STATUSES = new Set([rejected, toBeScheduled, canceled]);

const createOption = (text, handler) => ({ text, handler });

const InterviewDropdown = ({ interview, canUserEdit, canUserAssess }) => {
  const { id, status, isCurrentInterview, assessment } = interview;

  const { data: proposal, mutate: refreshProposal } = useProposalsRead();
  const { mutate: refreshProposalsList } = useProposalsList();
  const refreshProposals = useCallback(
    () => Promise.all([refreshProposal(), refreshProposalsList()]),
    [refreshProposal, refreshProposalsList]
  );

  const dispatch = useDispatch();

  // handlers
  const editInterview = useCallback(() => {
    dispatch(openInterviewEdit(id));
  }, [dispatch, id]);

  const editAssessment = useCallback(() => {
    dispatch(openInterviewAssessment(id, 'edit'));
  }, [dispatch, id]);

  const cancelInterviewProposal = useCallback(() => {
    dispatch(openCancelInterviewProposal(id));
  }, [dispatch, id]);

  const cancelInterview = useCallback(async () => {
    if (await isDialogCanceled(openCancelInterview(proposal))) return;

    try {
      await updateInterview(id, { status: canceled });

      await refreshProposals();
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [proposal, id, refreshProposals]);

  const skipInterview = useCallback(async () => {
    if (await isDialogCanceled(openSkipInterview())) return;

    try {
      await updateInterview(id, { status: skipped });

      await refreshProposals();
    } catch (error) {
      fetchErrorHandler(error);
    }
    return true;
  }, [id, refreshProposals]);

  const deleteInterview = useCallback(async () => {
    if (await isDialogCanceled(openDeleteInterview())) return;

    try {
      await client.execute({
        operationId: 'proposal_interviews_delete',
        parameters: { id },
      });

      await refreshProposals();
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [id, refreshProposals]);

  const actions = [];
  let deleteOption = null;

  if (canUserEdit) {
    actions.push(createOption(t`Edit Interview`, editInterview));

    if (status === scheduled && !assessment) {
      actions.push(createOption(t`Cancel Interview`, cancelInterview));
    }

    if (TO_BE_SCHEDULED_STATUSES.has(status)) {
      actions.push(createOption(t`Skip Interview`, skipInterview));
      if (!isCurrentInterview) deleteOption = createOption(t`Delete`, deleteInterview);
    }

    if (status === pending) {
      actions.push(createOption(t`Cancel Interview Proposal`, cancelInterviewProposal));
    }
  }

  if (assessment && canUserAssess)
    actions.push(createOption(t`Edit Assessment`, editAssessment));

  if (deleteOption) actions.push(deleteOption);

  return (
    actions.length > 0 && (
      <div className={styles.headerItem}>
        <ActionsDropdown actions={actions} />
      </div>
    )
  );
};

InterviewDropdown.propTypes = {
  interview: PropTypes.shape({
    id: PropTypes.number,
    isCurrentInterview: PropTypes.bool,
    status: PropTypes.string,
  }).isRequired,
  canUserAssess: PropTypes.bool.isRequired,
  canUserEdit: PropTypes.bool.isRequired,
  isUserRelatedToInterview: PropTypes.bool.isRequired,
};

export default memo(InterviewDropdown);
