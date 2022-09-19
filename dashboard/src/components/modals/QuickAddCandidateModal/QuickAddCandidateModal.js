import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { Modal, SwaggerForm } from '@components';

import { useFormProcessing, useGetElements } from './logicHooks';

const QuickAddCandidateModal = ({ modalData }) => {
  const { isOpen, toggle, addCandidate } = modalData;

  const {
    initialState,
    endpoints,
    processReadObject,
    processFormState,
    checkFormStateBeforeSave,
    onSubmitDone,
  } = useFormProcessing(toggle);

  const { inputs, buttons } = useGetElements(toggle);

  const { read, save, validate } = endpoints;

  const handleScroll = (event) => {
    // prevent propagation to parent 'AddCandidateToJob' modal
    event.stopPropagation();
  };

  return (
    <Modal
      isOpen={isOpen}
      title={t`Add Candidate to Job`}
      onClose={toggle}
      size='large'
      withFooter={false}
    >
      <div onScroll={handleScroll}>
        <SwaggerForm
          formId='candidateQuickForm'
          // endpoints
          operationId={save}
          readOperationId={read}
          validateOperationId={validate}
          // form processing
          processReadObject={processReadObject}
          processFormState={processFormState}
          checkFormStateBeforeSave={checkFormStateBeforeSave}
          onFormSubmitDone={onSubmitDone}
          initialState={initialState}
          onSaved={addCandidate}
          // render elements
          inputs={inputs}
          buttons={buttons}
        />
      </div>
    </Modal>
  );
};

QuickAddCandidateModal.propTypes = {
  modalData: PropTypes.shape({
    isOpen: PropTypes.bool,
    toggle: PropTypes.func,
    addCandidate: PropTypes.func,
  }).isRequired,
};

export default memo(QuickAddCandidateModal);
