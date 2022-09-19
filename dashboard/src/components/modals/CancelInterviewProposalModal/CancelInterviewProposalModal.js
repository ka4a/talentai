import React, { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import PropTypes from 'prop-types';

import { FormContextProvider } from '@components';
import { closeCancelInterviewProposal } from '@actions';
import { updateInterview, useInterviewRead } from '@swrAPI';
import { fetchErrorHandler } from '@utils';
import { INTERVIEW_STATUSES } from '@constants';

import CancelInterviewProposalModalContent from './components/CancelInterviewProposalModalContent';

function CancelInterviewProposalModal({ onAfterSubmit }) {
  const { isOpen, interviewId } = useSelector(({ modals }) => modals.cancelInterview);

  const { data: interview } = useInterviewRead(interviewId);

  const dispatch = useDispatch();

  const handleClose = useCallback(() => {
    dispatch(closeCancelInterviewProposal());
  }, [dispatch]);

  const handleSubmit = useCallback(
    async (form) => {
      try {
        await updateInterview(interviewId, {
          ...form,
          status: INTERVIEW_STATUSES.canceled,
        });
        await onAfterSubmit?.();
      } catch (error) {
        fetchErrorHandler(error);
      }
      handleClose();
    },
    [handleClose, interviewId, onAfterSubmit]
  );

  return (
    <FormContextProvider initialForm={INITIAL_FORM} onSubmit={handleSubmit}>
      <CancelInterviewProposalModalContent
        isOpen={isOpen}
        onClose={handleClose}
        timeslots={interview.timeslots}
      />
    </FormContextProvider>
  );
}

CancelInterviewProposalModal.propTypes = {
  onAfterSubmit: PropTypes.func,
};

CancelInterviewProposalModal.defaultProps = {
  onAfterSubmit: null,
};

const INITIAL_FORM = {
  preScheduleMsg: '',
};

export default CancelInterviewProposalModal;
