import React, { memo, useCallback, useMemo, useState } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { validateOnBackend } from '@utils';
import FormContextProvider from '@components/formContext/FormContextProvider';

import openConfirmDisableDialog from './openConfirmDisableDialog';
import JobPostingModal from '../JobPostingModal';
import JobPostingBlock from '../JobPostingBlock';
import {
  useHandleSavePosting,
  useHandleSwitchEnabled,
  useInitialJobPostingFormState,
  usePostingRead,
} from '../../hooks';
import { POSTING_TYPES, POSTING_STATUSES } from '../../constants';

function PrivateJobPosting(props) {
  const { job, isEditable, canEnable } = props;

  const postingSWR = usePostingRead(POSTING_TYPES.private);

  const [isModalOpen, setIsModalOpen] = useState(false);

  const isEnabled = Boolean(postingSWR.data?.isEnabled);
  const isExists = postingSWR.data != null;

  const statusInfoMap = useStatusInfoMap();

  const openModal = useCallback(() => setIsModalOpen(true), []);
  const closeModal = useCallback(() => setIsModalOpen(false), []);

  const handleSavePosting = useHandleSavePosting({
    jobId: job.id,
    operationId: isExists ? OPERATION_IDS.update : OPERATION_IDS.create,
    refresh: postingSWR.mutate,
    setIsModalOpen,
    isEnabled,
  });

  const handleSwitchEnabled = useHandleSwitchEnabled({
    createOperationId: OPERATION_IDS.create,
    updateOperationId: OPERATION_IDS.update,
    isPostingExists: isExists,
    mutate: postingSWR.mutate,
    openConfirmDisableDialog,
    isEnabled,
    job,
  });

  const initialForm = useInitialJobPostingFormState(job, postingSWR.data);

  const validate = isExists ? validateUpdate : validateCreate;

  const { publicUuid } = postingSWR.data || {};

  const link = publicUuid ? `${window.location.origin}/jobs/${publicUuid}` : '';

  return (
    <>
      <FormContextProvider
        initialForm={initialForm}
        onValidate={validate}
        onSubmit={handleSavePosting}
      >
        <JobPostingModal
          title={t`Private Posting`}
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      </FormContextProvider>

      <JobPostingBlock
        isEnabled={isEnabled}
        isEditable={isEditable}
        statusInfoMap={statusInfoMap}
        status={isEnabled ? POSTING_STATUSES.enabled : POSTING_STATUSES.disabled}
        title={t`Private Posting`}
        canEnable={canEnable}
        onEdit={openModal}
        onSwitchEnabled={handleSwitchEnabled}
        link={link}
      />
    </>
  );
}

PrivateJobPosting.propTypes = {
  refreshJob: PropTypes.func.isRequired,
  isEditable: PropTypes.bool,
  canEnable: PropTypes.bool,
  postingUuid: PropTypes.string,
  job: PropTypes.shape({
    id: PropTypes.number,
    publicUuid: PropTypes.string,
  }),
};

PrivateJobPosting.defaultProps = {
  postingUuid: null,
  isEditable: false,
  canEnable: false,
  job: {},
};

function useStatusInfoMap() {
  return useMemo(
    () => ({
      [POSTING_STATUSES.enabled]: {
        title: t`Enabled`,
        description: t`Share this private URL with selected people:`,
        variant: 'success',
      },
      [POSTING_STATUSES.disabled]: {
        title: t`Disabled`,
        description: t`Generate a private URL and share this job only with selected people.`,
        variant: 'neutral',
      },
    }),
    []
  );
}

const OPERATION_IDS = {
  validate_create: 'job_postings_private_validate_create',
  validate_update: 'job_postings_private_validate_partial_update',
  create: 'job_postings_private_create',
  update: 'job_postings_private_partial_update',
};

const validateCreate = (form) => validateOnBackend(OPERATION_IDS.validate_create, form);
const validateUpdate = (form) => validateOnBackend(OPERATION_IDS.validate_update, form);

export default memo(PrivateJobPosting);
