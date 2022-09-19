import React, { memo, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { t } from '@lingui/macro';

import { closeInterviewAssessment } from '@actions';
import { ButtonBar, Modal, SwaggerForm } from '@components';

import Inputs from './components/Inputs';
import useForm from './useForm';

import styles from './InterviewAssessmentModal.module.scss';

const initialState = {
  notes: '',
  decision: null,
  hiringCriteria: {},
};

const endpoints = {
  save: 'proposal_interview_assessment_create',
  read: 'proposal_interviews_read',
};

const InterviewAssessmentModal = () => {
  const { isOpen, interviewId, type } = useSelector(
    (state) => state.modals.interviewAssessment
  );

  const dispatch = useDispatch();

  const closeModal = useCallback(() => {
    dispatch(closeInterviewAssessment());
  }, [dispatch]);

  const title = useMemo(() => {
    const titles = { add: t`Add Assessment`, edit: t`Edit Assessment` };
    return titles[type] ?? '';
  }, [type]);

  const { processReadObject, processFormState, onSaved } = useForm(
    closeModal,
    interviewId
  );

  const isEditMode = type === 'edit';

  const inputs = useCallback(
    ({ FormInput, setValue }) => <Inputs FormInput={FormInput} setValue={setValue} />,
    []
  );

  const buttons = useCallback(
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

  return (
    <Modal isOpen={isOpen} onClose={closeModal} title={title} withFooter={false}>
      <SwaggerForm
        formId='interviewEdit'
        operationId={endpoints.save}
        readOperationId={isEditMode ? endpoints.read : null}
        // form processing
        editing={isEditMode ? interviewId : null}
        initialState={initialState}
        processReadObject={processReadObject}
        processFormState={processFormState}
        onSaved={onSaved}
        // render elements
        inputs={inputs}
        buttons={buttons}
      />
    </Modal>
  );
};

export default memo(InterviewAssessmentModal);
