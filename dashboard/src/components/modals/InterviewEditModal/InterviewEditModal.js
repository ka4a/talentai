import React, { memo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';
import { pick } from 'lodash';

import { closeInterviewEdit } from '@actions';
import { INTERVIEW_TYPES_CHOICES } from '@constants';
import { useProposalsRead, useStaffOptions } from '@swrAPI';
import { ButtonBar, Modal, SwaggerForm } from '@components';
import { useTranslatedChoices } from '@hooks';

import styles from './InterviewEditModal.module.scss';

const initialState = {
  interviewType: 'general',
  interviewer: '',
  description: '',
};

// Used for both Adding and Editing interview
const InterviewEditModal = () => {
  const { isOpen, interviewId } = useSelector((state) => state.modals.interviewEdit);
  const dispatch = useDispatch();

  const closeModal = useCallback(() => {
    dispatch(closeInterviewEdit());
  }, [dispatch]);

  const renderInputs = useRenderInputs();
  const renderButtons = useRenderButtons(closeModal);
  const handleSaved = useHandleSaved(closeModal);
  const processFormState = useProcessFormState();

  let title = '';
  if (isOpen) title = interviewId ? t`Edit Interview` : t`Add Interview`;

  const saveAction = interviewId ? 'partial_update' : 'create';

  return (
    <Modal
      isOpen={isOpen}
      onClose={closeModal}
      title={title}
      withFooter={false}
      withoutOverflow
    >
      <SwaggerForm
        formId='interviewEdit'
        operationId={`proposal_interviews_${saveAction}`}
        readOperationId='proposal_interviews_read'
        // form processing
        editing={interviewId}
        initialState={initialState}
        processReadObject={processReadObject}
        processFormState={processFormState}
        onSaved={handleSaved}
        // render elements
        inputs={renderInputs}
        buttons={renderButtons}
      />
    </Modal>
  );
};

const processReadObject = (interview) => ({
  ...pick(interview, ['id', 'description', 'interviewType']),
  interviewer: interview?.interviewer?.id ?? null,
});

function useHandleSaved(closeModal) {
  const { mutate: refreshProposal } = useProposalsRead();

  return useCallback(async () => {
    closeModal();
    await refreshProposal();
  }, [closeModal, refreshProposal]);
}

function useProcessFormState() {
  const { proposalId } = useParams();

  return useCallback(
    (form) => {
      delete form.timeslots;
      return {
        ...form,
        proposal: proposalId,
      };
    },
    [proposalId]
  );
}

function useRenderInputs() {
  const staffList = useStaffOptions();

  const { i18n } = useLingui();
  const interviewTypesChoices = useTranslatedChoices(i18n, INTERVIEW_TYPES_CHOICES);

  return useCallback(
    ({ FormInput }) => (
      <div className={styles.contentWrapper}>
        <div className={styles.row}>
          <FormInput
            type='select'
            name='interviewType'
            label={t`Type`}
            options={interviewTypesChoices}
          />
          <FormInput
            type='select'
            label={t`Interviewer`}
            name='interviewer'
            options={staffList}
          />
        </div>

        <FormInput type='rich-editor' label={t`Details`} name='description' />
      </div>
    ),
    [staffList, interviewTypesChoices]
  );
}

function useRenderButtons(closeModal) {
  return useCallback(
    (form, makeOnSubmit, { disabled }) => (
      <ButtonBar
        className={styles.buttonBar}
        onSave={makeOnSubmit()}
        onCancel={closeModal}
        isDisabled={disabled}
        isModal
      />
    ),
    [closeModal]
  );
}

export default memo(InterviewEditModal);
