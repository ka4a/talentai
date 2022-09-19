import React, { memo, useCallback, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';

import { validateOnBackend } from '@utils';
import FormContextProvider from '@components/formContext/FormContextProvider';
import { useCareerSiteUrl } from '@hooks';

import JobPostingModal from '../JobPostingModal';
import JobPostingBlock from '../JobPostingBlock';
import {
  useHandleSavePosting,
  useHandleSwitchEnabled,
  useInitialJobPostingFormState,
  usePostingRead,
} from '../../hooks';
import openConfirmDisableDialog from '../PrivateJobPosting/openConfirmDisableDialog';
import { POSTING_TYPES, POSTING_STATUSES } from '../../constants';

function CareerSiteJobPosting(props) {
  const { job, isEditable, canEnable } = props;

  const isCareerSiteEnabled = useSelector(
    (state) => state.user.profile.org.isCareerSiteEnabled
  );
  const careerSiteUrl = useCareerSiteUrl();

  const postingSWR = usePostingRead(POSTING_TYPES.career);

  const { isEnabled = false, slug } = postingSWR.data || {};
  const isExists = postingSWR.data != null;
  const link = slug ? `${careerSiteUrl}/${slug}` : '';

  const [isModalOpen, setIsModalOpen] = useState(false);

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

  const statusInfoMap = useStatusInfoMap(careerSiteUrl);

  const openModal = useCallback(() => setIsModalOpen(true), []);
  const closeModal = useCallback(() => setIsModalOpen(false), []);

  const initialForm = useInitialJobPostingFormState(job, postingSWR.data);

  let status = isEnabled ? POSTING_STATUSES.enabled : POSTING_STATUSES.disabled;

  if (!isCareerSiteEnabled) status = POSTING_STATUSES.careerSiteDisabled;

  const validate = isExists ? validateUpdate : validateCreate;

  return (
    <>
      <FormContextProvider
        initialForm={initialForm}
        onValidate={validate}
        onSubmit={handleSavePosting}
      >
        <JobPostingModal
          title={t`Job Posting - Career Site`}
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      </FormContextProvider>

      <JobPostingBlock
        title={t`Career Site`}
        isEnabled={isEnabled && isCareerSiteEnabled}
        isEditable={isEditable}
        canEnable={canEnable && isCareerSiteEnabled}
        status={status}
        statusInfoMap={statusInfoMap}
        onEdit={openModal}
        onSwitchEnabled={handleSwitchEnabled}
        link={link}
      />
    </>
  );
}

CareerSiteJobPosting.propTypes = {
  refreshJob: PropTypes.func.isRequired,
  isEditable: PropTypes.bool,
  canEnable: PropTypes.bool,
  postingUuid: PropTypes.string,
  job: PropTypes.shape({
    id: PropTypes.number,
    publicUuid: PropTypes.string,
  }),
};

CareerSiteJobPosting.defaultProps = {
  postingUuid: null,
  isEditable: false,
  canEnable: false,
  job: {},
};

function useStatusInfoMap(careerSiteUrl) {
  return useMemo(
    () => ({
      [POSTING_STATUSES.enabled]: {
        title: t`Published`,
        description: t`Your job posting is listed on your company Career Site here:`,
        variant: 'success',
      },
      [POSTING_STATUSES.disabled]: {
        title: t`Unpublished`,
        description: (
          <Trans>
            Post your job on your company <a href={careerSiteUrl}>Career Site</a> and
            make it visible to anyone.
          </Trans>
        ),
        variant: 'neutral',
      },
      [POSTING_STATUSES.careerSiteDisabled]: {
        title: t`Career Site Disabled`,
        description: t`Your company must first enable your company Career Site in order to publish your job.`,
        variant: 'warning',
      },
    }),
    [careerSiteUrl]
  );
}

const OPERATION_IDS = {
  validate_create: 'job_postings_career_validate_create',
  validate_update: 'job_postings_career_validate_partial_update',
  create: 'job_postings_career_create',
  update: 'job_postings_career_partial_update',
};

const validateCreate = (form) => validateOnBackend(OPERATION_IDS.validate_create, form);
const validateUpdate = (form) => validateOnBackend(OPERATION_IDS.validate_update, form);

export default memo(CareerSiteJobPosting);
