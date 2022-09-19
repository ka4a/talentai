import React, { memo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { t } from '@lingui/macro';

import { Modal, SwaggerForm } from '@components';
import { closeInterviewScheduling } from '@actions';
import { addFieldRow, removeFieldRow } from '@utils';

import {
  useOnSaved,
  useProcessFormState,
  useProcessReadObject,
  useRenderButtons,
  useRenderInputs,
} from './hooks';

const initialState = {
  interviewer: null,
  notes: '',
  sourceTimeslots: [{ localId: 0, date: null, startAt: null, endAt: null }],
};

const stateBoundHandlers = {
  addFieldRow,
  removeFieldRow,
};

const InterviewSchedulingModal = ({ proposal }) => {
  const { isOpen, interviewId } = useSelector(
    (state) => state.modals.interviewScheduling
  );

  const dispatch = useDispatch();

  const closeModal = useCallback(() => {
    dispatch(closeInterviewScheduling());
  }, [dispatch]);

  const processFormState = useProcessFormState(proposal.id);
  const processReadObject = useProcessReadObject(proposal.candidate);
  const onSaved = useOnSaved(closeModal);

  const renderButtons = useRenderButtons(closeModal);
  const renderInputs = useRenderInputs(proposal.candidate);

  return (
    <Modal
      isOpen={isOpen}
      onClose={closeModal}
      title={t`Schedule Interview`}
      withFooter={false}
    >
      <SwaggerForm
        formId='interviewScheduling'
        readOperationId='proposal_interviews_read'
        operationId='proposal_interviews_partial_update'
        // form processing
        editing={interviewId}
        initialState={initialState}
        processReadObject={processReadObject}
        processFormState={processFormState}
        handlers={stateBoundHandlers}
        onSaved={onSaved}
        // render elements
        inputs={renderInputs}
        buttons={renderButtons}
      />
    </Modal>
  );
};

export default memo(InterviewSchedulingModal);
