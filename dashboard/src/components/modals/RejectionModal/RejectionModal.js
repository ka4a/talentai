import React, { memo, useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { useBoolean } from 'react-use';

import { t, Trans } from '@lingui/macro';

import { client } from '@client';
import { closeRejection } from '@actions';
import { fetchErrorHandler } from '@utils';
import { useProposalsList, useProposalsRead } from '@swrAPI';
import { LabeledInput, LabeledSelect, Modal, Typography } from '@components';

import styles from './RejectionModal.module.scss';

export const REJECTED_BY = [
  { value: 'company', name: t`Rejected by Company` },
  { value: 'candidate', name: t`Rejected by Candidate` },
];

const RejectionModal = () => {
  const { isOpen } = useSelector((state) => state.modals.rejection);
  const { proposalReasonsDeclined, proposalReasonsNotInterested } = useSelector(
    (state) => state.settings.localeData
  );

  const { proposalId } = useParams();

  const { mutate: refreshProposal } = useProposalsRead();
  const { mutate: refreshProposalList } = useProposalsList();

  const dispatch = useDispatch();
  const handleClose = useCallback(() => {
    dispatch(closeRejection());
  }, [dispatch]);

  const [rejectedBy, setRejectedBy] = useState(null);
  const [rejectionReason, setRejectionReason] = useState(null);
  const [other, setOther] = useState(null);
  const [isError, toggleError] = useBoolean(false);

  const handleChangeInput = useCallback((e) => {
    setOther(e.target.value);
  }, []);

  useEffect(() => {
    setRejectionReason(null);
  }, [rejectedBy]);

  useEffect(() => {
    setOther(null);
  }, [rejectionReason]);

  useEffect(() => {
    if (!isOpen) {
      setRejectedBy(null);
      setRejectionReason(null);
      setOther(null);
    }
  }, [isOpen]);

  useEffect(() => {
    toggleError(false);
  }, [toggleError, rejectedBy, rejectionReason, other]);

  const reasonsOptions =
    rejectedBy === 'company' ? proposalReasonsDeclined : proposalReasonsNotInterested;

  const validateFields = useCallback(() => {
    const isReasonOther = reasonsOptions.find((el) => el.value === rejectionReason)
      ?.hasDescription;

    if (!rejectedBy || !rejectionReason || (isReasonOther && !other)) {
      toggleError(true);
      return false;
    }

    return true;
  }, [other, reasonsOptions, rejectedBy, rejectionReason, toggleError]);

  const confirmRejection = useCallback(async () => {
    const isValid = validateFields();
    if (!isValid) return;

    try {
      const data = { isRejected: true };

      const rejectedByCompany = rejectedBy === 'company';
      const reasonKey = rejectedByCompany ? 'declineReasons' : 'reasonsNotInterested';
      const otherKey = rejectedByCompany
        ? 'reasonDeclinedDescription'
        : 'reasonNotInterestedDescription';

      data[reasonKey] = [rejectionReason];
      if (other) data[otherKey] = other;

      await client.execute({
        operationId: 'proposals_partial_update',
        parameters: {
          id: proposalId,
          data,
        },
      });

      await Promise.all([refreshProposal(), refreshProposalList()]);

      handleClose();
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [
    handleClose,
    other,
    proposalId,
    refreshProposal,
    refreshProposalList,
    rejectedBy,
    rejectionReason,
    validateFields,
  ]);

  const selectedReason = reasonsOptions.find((el) => el.value === rejectionReason);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      onCancel={handleClose}
      onSave={confirmRejection}
      title={t`Reject Candidate`}
      saveText={t`Confirm Rejection`}
      withoutOverflow
      size='small'
    >
      <div className={styles.wrapper}>
        <LabeledSelect
          label={t`Rejected by`}
          value={rejectedBy}
          onChange={setRejectedBy}
          options={REJECTED_BY}
          required
        />

        {rejectedBy && (
          <div className={styles.topGap}>
            <LabeledSelect
              key={rejectionReason}
              labelKey='label'
              label={t`Reason`}
              value={rejectionReason}
              onChange={setRejectionReason}
              options={reasonsOptions}
              required
            />
          </div>
        )}

        {selectedReason?.hasDescription && (
          <div className={styles.topGap}>
            <LabeledInput
              value={other}
              onChange={handleChangeInput}
              label={t`Other`}
              required
            />
          </div>
        )}

        {isError && (
          <Typography className={styles.error} variant='caption'>
            <Trans>You must add this field</Trans>
          </Typography>
        )}
      </div>
    </Modal>
  );
};

export default memo(RejectionModal);
